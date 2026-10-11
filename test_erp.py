"""
test_erp.py - Automated checks. Run with:  python test_erp.py
Uses a temporary in-memory database, so it never touches retail_erp.db.
"""
import erp


def fresh():
    conn = erp.connect(":memory:")
    erp.init_db(conn)
    erp.seed_demo_data(conn)
    return conn


def stock(conn, pid):
    return conn.execute("SELECT stock_qty FROM products WHERE product_id=?", (pid,)).fetchone()[0]


def expect_error(fn, label):
    try:
        fn()
    except ValueError as e:
        print(f"  PASS  {label}  ->  {e}")
        return
    raise AssertionError(f"FAILED (no error raised): {label}")


def run():
    conn = fresh()

    # 1. Integration: one order touches Sales, Inventory and Finance
    before = stock(conn, 1)
    order_id, total = erp.place_order(conn, 1, [(1, 2), (2, 3)])
    assert total == 2 * 25000 + 3 * 4500
    assert stock(conn, 1) == before - 2, "stock must go down"
    inv = conn.execute("SELECT * FROM invoices WHERE order_id=?", (order_id,)).fetchone()
    assert inv and inv["amount_due"] == total and inv["status"] == "UNPAID"
    moves = conn.execute("SELECT COUNT(*) FROM stock_movements WHERE order_id=?", (order_id,)).fetchone()[0]
    assert moves == 2
    print("  PASS  order updates stock, creates invoice, logs movements")

    # 2. Rollback: failing order must leave NOTHING behind
    orders_before = conn.execute("SELECT COUNT(*) FROM sales_orders").fetchone()[0]
    stock5_before, stock1_before = stock(conn, 5), stock(conn, 1)
    expect_error(lambda: erp.place_order(conn, 1, [(1, 1), (5, 999)]), "insufficient stock rejected")
    assert conn.execute("SELECT COUNT(*) FROM sales_orders").fetchone()[0] == orders_before
    assert stock(conn, 1) == stock1_before and stock(conn, 5) == stock5_before
    print("  PASS  failed order fully rolled back (no half-finished data)")

    # 3. Validation rules
    expect_error(lambda: erp.add_product(conn, "RICE-5KG", "Dup", 100, 1), "duplicate SKU rejected")
    expect_error(lambda: erp.add_product(conn, "X1", "Bad price", -5, 1), "negative price rejected")
    expect_error(lambda: erp.add_customer(conn, "Copy", "0700111222"), "duplicate phone rejected")
    expect_error(lambda: erp.place_order(conn, 1, [(1, 0)]), "zero quantity rejected")
    expect_error(lambda: erp.place_order(conn, 99, [(1, 1)]), "unknown customer rejected")
    expect_error(lambda: erp.delete_product(conn, 1), "cannot delete product with history")
    expect_error(lambda: erp.delete_customer(conn, 1), "cannot delete customer with orders")

    # 4. Payments
    _, _, bal = erp.invoice_balance(conn, inv["invoice_id"])
    erp.record_payment(conn, inv["invoice_id"], 10000, "CASH")
    assert erp.invoice_balance(conn, inv["invoice_id"])[0]["status"] == "PARTIAL"
    expect_error(lambda: erp.record_payment(conn, inv["invoice_id"], bal, "CASH"), "overpayment rejected")
    erp.record_payment(conn, inv["invoice_id"], bal - 10000, "MOBILE_MONEY")
    assert erp.invoice_balance(conn, inv["invoice_id"])[0]["status"] == "PAID"
    expect_error(lambda: erp.cancel_order(conn, order_id), "cannot cancel a paid order")
    print("  PASS  partial then full payment updates invoice status")

    # 5. Cancel an unpaid order: stock returns, invoice voided
    oid2, _ = erp.place_order(conn, 2, [(3, 4)])
    s_mid = stock(conn, 3)
    erp.cancel_order(conn, oid2)
    assert stock(conn, 3) == s_mid + 4
    assert conn.execute("SELECT status FROM invoices WHERE order_id=?", (oid2,)).fetchone()[0] == "VOID"
    expect_error(lambda: erp.record_payment(conn, 2, 100, "CASH"), "cannot pay a voided invoice")
    print("  PASS  cancel returns stock and voids invoice")

    # 6. Consistency audit: stock on hand must equal the sum of its movement history
    for p in erp.list_products(conn):
        moved = conn.execute("SELECT COALESCE(SUM(change_qty),0) FROM stock_movements WHERE product_id=?",
                             (p["product_id"],)).fetchone()[0]
        assert p["stock_qty"] == moved, f"{p['name']}: stock {p['stock_qty']} != movements {moved}"
    print("  PASS  stock levels reconcile with movement history for every product")
    print("\nALL TESTS PASSED")


if __name__ == "__main__":
    run()
