"""
erp.py - Business logic for the Retail ERP prototype.

All three modules (Inventory, Sales, Finance) read and write the SAME
SQLite database (retail_erp.db). The key integration is place_order():
one sale updates Sales tables, reduces Inventory stock, and creates a
Finance invoice, all inside ONE database transaction (all-or-nothing).
"""
import os
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "retail_erp.db")
SCHEMA_PATH = os.path.join(HERE, "schema.sql")


# ------------------------------------------------------------------
# Database setup
# ------------------------------------------------------------------
def connect(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row          # lets us use row["name"]
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn):
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()


def seed_demo_data(conn):
    """Adds sample products and customers if the database is empty."""
    if conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] > 0:
        return False
    products = [
        ("RICE-5KG", "Rice 5kg", 25000, 40, 10),
        ("SUGAR-1KG", "Sugar 1kg", 4500, 60, 15),
        ("OIL-1L", "Cooking Oil 1L", 9000, 30, 10),
        ("SOAP-BAR", "Soap Bar", 2500, 100, 20),
        ("MILK-500", "Milk 500ml", 2000, 8, 10),
    ]
    customers = [
        ("Amina Nakato", "0700111222", "amina@example.com"),
        ("John Okello", "0700333444", None),
    ]
    with conn:
        for sku, name, price, stock, reorder in products:
            cur = conn.execute(
                "INSERT INTO products (sku,name,unit_price,stock_qty,reorder_level) "
                "VALUES (?,?,?,?,?)", (sku, name, price, stock, reorder))
            # log opening stock so stock_qty always equals the sum of movements
            conn.execute("INSERT INTO stock_movements (product_id,change_qty,reason) "
                         "VALUES (?,?,'RESTOCK')", (cur.lastrowid, stock))
        conn.executemany(
            "INSERT INTO customers (name,phone,email) VALUES (?,?,?)", customers)
    return True


# ------------------------------------------------------------------
# INVENTORY MODULE - CRUD
# ------------------------------------------------------------------
def add_product(conn, sku, name, price, stock, reorder=5):
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO products (sku,name,unit_price,stock_qty,reorder_level) "
                "VALUES (?,?,?,?,?)", (sku.strip().upper(), name, price, stock, reorder))
            if stock > 0:
                conn.execute(
                    "INSERT INTO stock_movements (product_id,change_qty,reason) "
                    "VALUES (?,?,'RESTOCK')", (cur.lastrowid, stock))
        return cur.lastrowid
    except sqlite3.IntegrityError as e:
        raise ValueError(f"Could not add product (duplicate SKU or invalid value): {e}")


def list_products(conn):
    return conn.execute("SELECT * FROM products ORDER BY product_id").fetchall()


def update_product(conn, product_id, name=None, price=None, reorder=None):
    p = conn.execute("SELECT * FROM products WHERE product_id=?", (product_id,)).fetchone()
    if not p:
        raise ValueError("Product not found.")
    try:
        with conn:
            conn.execute(
                "UPDATE products SET name=?, unit_price=?, reorder_level=? WHERE product_id=?",
                (name or p["name"],
                 price if price is not None else p["unit_price"],
                 reorder if reorder is not None else p["reorder_level"],
                 product_id))
    except sqlite3.IntegrityError as e:
        raise ValueError(f"Invalid value: {e}")


def restock_product(conn, product_id, qty):
    if qty <= 0:
        raise ValueError("Restock quantity must be positive.")
    if not conn.execute("SELECT 1 FROM products WHERE product_id=?", (product_id,)).fetchone():
        raise ValueError("Product not found.")
    with conn:
        conn.execute("UPDATE products SET stock_qty = stock_qty + ? WHERE product_id=?",
                     (qty, product_id))
        conn.execute("INSERT INTO stock_movements (product_id,change_qty,reason) "
                     "VALUES (?,?,'RESTOCK')", (product_id, qty))


def delete_product(conn, product_id):
    try:
        with conn:
            cur = conn.execute("DELETE FROM products WHERE product_id=?", (product_id,))
        if cur.rowcount == 0:
            raise ValueError("Product not found.")
    except sqlite3.IntegrityError:
        raise ValueError("Cannot delete: this product has sales/stock history. "
                         "(Foreign key protects the records.)")


def low_stock(conn):
    return conn.execute(
        "SELECT * FROM products WHERE stock_qty <= reorder_level ORDER BY stock_qty").fetchall()


# ------------------------------------------------------------------
# SALES MODULE - customers CRUD
# ------------------------------------------------------------------
def add_customer(conn, name, phone, email=None):
    try:
        with conn:
            cur = conn.execute("INSERT INTO customers (name,phone,email) VALUES (?,?,?)",
                               (name.strip(), phone.strip(), email))
        return cur.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError("Customer not added: name is empty or phone already exists.")


def list_customers(conn):
    return conn.execute("SELECT * FROM customers ORDER BY customer_id").fetchall()


def update_customer(conn, customer_id, name=None, phone=None, email=None):
    c = conn.execute("SELECT * FROM customers WHERE customer_id=?", (customer_id,)).fetchone()
    if not c:
        raise ValueError("Customer not found.")
    try:
        with conn:
            conn.execute("UPDATE customers SET name=?, phone=?, email=? WHERE customer_id=?",
                         (name or c["name"], phone or c["phone"],
                          email if email is not None else c["email"], customer_id))
    except sqlite3.IntegrityError:
        raise ValueError("Update failed: that phone number already belongs to another customer.")


def delete_customer(conn, customer_id):
    try:
        with conn:
            cur = conn.execute("DELETE FROM customers WHERE customer_id=?", (customer_id,))
        if cur.rowcount == 0:
            raise ValueError("Customer not found.")
    except sqlite3.IntegrityError:
        raise ValueError("Cannot delete: this customer has orders on record.")


# ------------------------------------------------------------------
# THE INTEGRATION POINT: Sales -> Inventory -> Finance in one transaction
# ------------------------------------------------------------------
def place_order(conn, customer_id, items):
    """
    items = [(product_id, quantity), ...]
    1. SALES:      create the order and its order lines
    2. INVENTORY:  reduce stock and log a stock movement
    3. FINANCE:    create an UNPAID invoice for the total
    If ANYTHING fails (e.g. not enough stock) the whole thing is rolled back,
    so the three modules can never disagree with each other.
    """
    if not items:
        raise ValueError("An order needs at least one item.")
    if not conn.execute("SELECT 1 FROM customers WHERE customer_id=?", (customer_id,)).fetchone():
        raise ValueError("Customer not found.")

    # merge duplicate lines for the same product
    merged = {}
    for pid, qty in items:
        merged[pid] = merged.get(pid, 0) + qty

    try:
        with conn:  # begins a transaction; commits on success, rolls back on error
            order_id = conn.execute(
                "INSERT INTO sales_orders (customer_id,total_amount) VALUES (?,0)",
                (customer_id,)).lastrowid
            total = 0.0
            for pid, qty in merged.items():
                if qty <= 0:
                    raise ValueError("Quantity must be greater than zero.")
                p = conn.execute("SELECT * FROM products WHERE product_id=?", (pid,)).fetchone()
                if not p:
                    raise ValueError(f"Product {pid} not found.")
                if p["stock_qty"] < qty:
                    raise ValueError(
                        f"Not enough stock for '{p['name']}': "
                        f"requested {qty}, available {p['stock_qty']}.")
                # Sales: order line (price is copied so later price changes don't alter history)
                conn.execute(
                    "INSERT INTO order_items (order_id,product_id,quantity,unit_price) "
                    "VALUES (?,?,?,?)", (order_id, pid, qty, p["unit_price"]))
                # Inventory: reduce stock + audit trail
                conn.execute("UPDATE products SET stock_qty = stock_qty - ? WHERE product_id=?",
                             (qty, pid))
                conn.execute(
                    "INSERT INTO stock_movements (product_id,change_qty,reason,order_id) "
                    "VALUES (?,?,'SALE',?)", (pid, -qty, order_id))
                total += qty * p["unit_price"]
            # Sales: store total.  Finance: create invoice.
            conn.execute("UPDATE sales_orders SET total_amount=? WHERE order_id=?", (total, order_id))
            conn.execute("INSERT INTO invoices (order_id,amount_due) VALUES (?,?)", (order_id, total))
        return order_id, total
    except sqlite3.IntegrityError as e:
        raise ValueError(f"Order rejected by database rules: {e}")


def cancel_order(conn, order_id):
    """Cancel: return stock to Inventory and void the Finance invoice."""
    o = conn.execute("SELECT * FROM sales_orders WHERE order_id=?", (order_id,)).fetchone()
    if not o:
        raise ValueError("Order not found.")
    if o["status"] == "CANCELLED":
        raise ValueError("Order is already cancelled.")
    paid = conn.execute(
        "SELECT COALESCE(SUM(p.amount),0) FROM payments p JOIN invoices i "
        "ON p.invoice_id=i.invoice_id WHERE i.order_id=?", (order_id,)).fetchone()[0]
    if paid > 0:
        raise ValueError("Cannot cancel: payments already recorded (a refund process would be needed).")
    with conn:
        for it in conn.execute("SELECT * FROM order_items WHERE order_id=?", (order_id,)).fetchall():
            conn.execute("UPDATE products SET stock_qty = stock_qty + ? WHERE product_id=?",
                         (it["quantity"], it["product_id"]))
            conn.execute(
                "INSERT INTO stock_movements (product_id,change_qty,reason,order_id) "
                "VALUES (?,?,'CANCEL_RETURN',?)", (it["product_id"], it["quantity"], order_id))
        conn.execute("UPDATE sales_orders SET status='CANCELLED' WHERE order_id=?", (order_id,))
        conn.execute("UPDATE invoices SET status='VOID' WHERE order_id=?", (order_id,))


def list_orders(conn):
    return conn.execute(
        "SELECT o.order_id, c.name AS customer, o.order_date, o.status, o.total_amount, "
        "i.invoice_id, i.status AS invoice_status "
        "FROM sales_orders o JOIN customers c ON c.customer_id=o.customer_id "
        "LEFT JOIN invoices i ON i.order_id=o.order_id ORDER BY o.order_id").fetchall()


def order_detail(conn, order_id):
    return conn.execute(
        "SELECT p.name, oi.quantity, oi.unit_price, oi.quantity*oi.unit_price AS line_total "
        "FROM order_items oi JOIN products p ON p.product_id=oi.product_id "
        "WHERE oi.order_id=?", (order_id,)).fetchall()


# ------------------------------------------------------------------
# FINANCE MODULE
# ------------------------------------------------------------------
def invoice_balance(conn, invoice_id):
    inv = conn.execute("SELECT * FROM invoices WHERE invoice_id=?", (invoice_id,)).fetchone()
    if not inv:
        raise ValueError("Invoice not found.")
    paid = conn.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE invoice_id=?",
                        (invoice_id,)).fetchone()[0]
    return inv, paid, inv["amount_due"] - paid


def record_payment(conn, invoice_id, amount, method):
    inv, paid, balance = invoice_balance(conn, invoice_id)
    if inv["status"] == "VOID":
        raise ValueError("Cannot pay a voided invoice.")
    if amount <= 0:
        raise ValueError("Payment must be greater than zero.")
    if amount > balance + 1e-9:
        raise ValueError(f"Overpayment: balance on this invoice is only {balance:,.0f}.")
    new_status = "PAID" if abs(amount - balance) < 1e-9 else "PARTIAL"
    try:
        with conn:
            conn.execute("INSERT INTO payments (invoice_id,amount,method) VALUES (?,?,?)",
                         (invoice_id, amount, method))
            conn.execute("UPDATE invoices SET status=? WHERE invoice_id=?", (new_status, invoice_id))
    except sqlite3.IntegrityError as e:
        raise ValueError(f"Payment rejected: {e}")


def list_invoices(conn):
    return conn.execute(
        "SELECT i.invoice_id, i.order_id, c.name AS customer, i.amount_due, i.status, "
        "COALESCE((SELECT SUM(amount) FROM payments p WHERE p.invoice_id=i.invoice_id),0) AS paid "
        "FROM invoices i JOIN sales_orders o ON o.order_id=i.order_id "
        "JOIN customers c ON c.customer_id=o.customer_id ORDER BY i.invoice_id").fetchall()


def sales_summary(conn):
    return conn.execute(
        "SELECT COUNT(*) AS orders, COALESCE(SUM(total_amount),0) AS revenue "
        "FROM sales_orders WHERE status='CONFIRMED'").fetchone()


def outstanding_receivables(conn):
    return conn.execute(
        "SELECT COALESCE(SUM(i.amount_due - COALESCE((SELECT SUM(amount) FROM payments p "
        "WHERE p.invoice_id=i.invoice_id),0)),0) FROM invoices i "
        "WHERE i.status IN ('UNPAID','PARTIAL')").fetchone()[0]


def stock_history(conn, product_id):
    return conn.execute(
        "SELECT moved_at, change_qty, reason, order_id FROM stock_movements "
        "WHERE product_id=? ORDER BY movement_id", (product_id,)).fetchall()
