"""
app.py - Command-line menu for the Retail ERP prototype.
Run with:  python app.py
"""
import erp


# ---------- small input helpers ----------
def ask(prompt):
    return input(prompt).strip()


def ask_int(prompt):
    while True:
        try:
            return int(ask(prompt))
        except ValueError:
            print("  Please enter a whole number.")


def ask_float(prompt):
    while True:
        try:
            return float(ask(prompt))
        except ValueError:
            print("  Please enter a number.")


def money(x):
    return f"{x:,.0f}"


def safe(action):
    """Run an action; show business-rule errors nicely instead of crashing."""
    try:
        action()
    except ValueError as e:
        print(f"  ERROR: {e}")


# ---------- display helpers ----------
def show_products(conn):
    print(f"\n{'ID':<4}{'SKU':<12}{'Name':<20}{'Price':>9}{'Stock':>7}{'Reorder':>9}")
    for p in erp.list_products(conn):
        flag = "  <-- LOW" if p["stock_qty"] <= p["reorder_level"] else ""
        print(f"{p['product_id']:<4}{p['sku']:<12}{p['name']:<20}{money(p['unit_price']):>9}"
              f"{p['stock_qty']:>7}{p['reorder_level']:>9}{flag}")


def show_customers(conn):
    print(f"\n{'ID':<4}{'Name':<22}{'Phone':<14}Email")
    for c in erp.list_customers(conn):
        print(f"{c['customer_id']:<4}{c['name']:<22}{c['phone']:<14}{c['email'] or ''}")


def show_orders(conn):
    print(f"\n{'Order':<7}{'Customer':<20}{'Date':<20}{'Status':<11}{'Total':>10}  Invoice")
    for o in erp.list_orders(conn):
        print(f"{o['order_id']:<7}{o['customer']:<20}{o['order_date']:<20}{o['status']:<11}"
              f"{money(o['total_amount']):>10}  #{o['invoice_id']} ({o['invoice_status']})")


def show_invoices(conn):
    print(f"\n{'Inv':<5}{'Order':<7}{'Customer':<20}{'Due':>10}{'Paid':>10}  Status")
    for i in erp.list_invoices(conn):
        print(f"{i['invoice_id']:<5}{i['order_id']:<7}{i['customer']:<20}"
              f"{money(i['amount_due']):>10}{money(i['paid']):>10}  {i['status']}")


# ---------- menu actions ----------
def do_add_product(conn):
    sku = ask("  SKU (e.g. TEA-250): ")
    name = ask("  Name: ")
    price = ask_float("  Unit price: ")
    stock = ask_int("  Opening stock: ")
    reorder = ask_int("  Reorder level: ")
    pid = erp.add_product(conn, sku, name, price, stock, reorder)
    print(f"  Product added with ID {pid}.")


def do_update_product(conn):
    show_products(conn)
    pid = ask_int("  Product ID to update: ")
    name = ask("  New name (blank = keep): ") or None
    price = ask("  New price (blank = keep): ")
    reorder = ask("  New reorder level (blank = keep): ")
    erp.update_product(conn, pid, name,
                       float(price) if price else None,
                       int(reorder) if reorder else None)
    print("  Product updated.")


def do_restock(conn):
    show_products(conn)
    erp.restock_product(conn, ask_int("  Product ID: "), ask_int("  Quantity received: "))
    print("  Stock updated.")


def do_delete_product(conn):
    show_products(conn)
    erp.delete_product(conn, ask_int("  Product ID to delete: "))
    print("  Product deleted.")


def do_add_customer(conn):
    cid = erp.add_customer(conn, ask("  Name: "), ask("  Phone: "), ask("  Email (optional): ") or None)
    print(f"  Customer added with ID {cid}.")


def do_update_customer(conn):
    show_customers(conn)
    cid = ask_int("  Customer ID to update: ")
    erp.update_customer(conn, cid, ask("  New name (blank = keep): ") or None,
                        ask("  New phone (blank = keep): ") or None,
                        ask("  New email (blank = keep): ") or None)
    print("  Customer updated.")


def do_delete_customer(conn):
    show_customers(conn)
    erp.delete_customer(conn, ask_int("  Customer ID to delete: "))
    print("  Customer deleted.")


def do_place_order(conn):
    show_customers(conn)
    cid = ask_int("  Customer ID: ")
    show_products(conn)
    items = []
    print("  Add items (enter product ID 0 to finish).")
    while True:
        pid = ask_int("  Product ID: ")
        if pid == 0:
            break
        items.append((pid, ask_int("  Quantity: ")))
    order_id, total = erp.place_order(conn, cid, items)
    print(f"  Order #{order_id} created. Total {money(total)}. "
          f"Stock reduced and invoice generated automatically.")


def do_cancel_order(conn):
    show_orders(conn)
    erp.cancel_order(conn, ask_int("  Order ID to cancel: "))
    print("  Order cancelled: stock returned, invoice voided.")


def do_order_detail(conn):
    show_orders(conn)
    oid = ask_int("  Order ID: ")
    print(f"\n{'Product':<22}{'Qty':>5}{'Price':>10}{'Line total':>12}")
    for r in erp.order_detail(conn, oid):
        print(f"{r['name']:<22}{r['quantity']:>5}{money(r['unit_price']):>10}{money(r['line_total']):>12}")


def do_payment(conn):
    show_invoices(conn)
    iid = ask_int("  Invoice ID: ")
    _, _, balance = erp.invoice_balance(conn, iid)
    print(f"  Balance on invoice: {money(balance)}")
    amount = ask_float("  Payment amount: ")
    method = ask("  Method (CASH / MOBILE_MONEY / CARD): ").upper()
    erp.record_payment(conn, iid, amount, method)
    print("  Payment recorded.")


def do_stock_history(conn):
    show_products(conn)
    pid = ask_int("  Product ID: ")
    print(f"\n{'When':<22}{'Change':>8}  {'Reason':<15}Order")
    for m in erp.stock_history(conn, pid):
        print(f"{m['moved_at']:<22}{m['change_qty']:>+8}  {m['reason']:<15}{m['order_id'] or ''}")


def do_reports(conn):
    s = erp.sales_summary(conn)
    print(f"\n  Confirmed orders: {s['orders']}")
    print(f"  Total revenue:    {money(s['revenue'])}")
    print(f"  Money still owed (receivables): {money(erp.outstanding_receivables(conn))}")
    low = erp.low_stock(conn)
    print(f"  Products at/below reorder level: {len(low)}")
    for p in low:
        print(f"     - {p['name']} (stock {p['stock_qty']}, reorder at {p['reorder_level']})")


MENU = {
    "INVENTORY": [
        ("1", "View products", lambda c: show_products(c)),
        ("2", "Add product", do_add_product),
        ("3", "Update product", do_update_product),
        ("4", "Restock product", do_restock),
        ("5", "Delete product", do_delete_product),
        ("6", "Stock movement history", do_stock_history),
    ],
    "SALES": [
        ("7", "View customers", lambda c: show_customers(c)),
        ("8", "Add customer", do_add_customer),
        ("9", "Update customer", do_update_customer),
        ("10", "Delete customer", do_delete_customer),
        ("11", "Place order  (updates stock + creates invoice)", do_place_order),
        ("12", "View orders", lambda c: show_orders(c)),
        ("13", "View order details", do_order_detail),
        ("14", "Cancel order (returns stock + voids invoice)", do_cancel_order),
    ],
    "FINANCE": [
        ("15", "View invoices", lambda c: show_invoices(c)),
        ("16", "Record payment", do_payment),
        ("17", "Summary report", do_reports),
    ],
}


def main():
    conn = erp.connect()
    erp.init_db(conn)
    if erp.seed_demo_data(conn):
        print("First run: sample products and customers loaded.")
    actions = {key: fn for section in MENU.values() for key, _, fn in section}
    while True:
        print("\n========== RETAIL ERP ==========")
        for section, entries in MENU.items():
            print(f"-- {section} --")
            for key, label, _ in entries:
                print(f"  {key:>2}. {label}")
        print("   0. Exit")
        choice = ask("Choose: ")
        if choice == "0":
            print("Goodbye.")
            break
        if choice in actions:
            safe(lambda: actions[choice](conn))
        else:
            print("  Invalid choice.")


if __name__ == "__main__":
    main()
