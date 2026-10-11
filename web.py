"""
web.py - Web dashboard for the Retail ERP prototype.

Uses ONLY Python's standard library (no installs). It talks to the SAME
database and the SAME business-logic functions (erp.py) as the terminal
version, so both interfaces always agree.

Run with:  py web.py      then open  http://localhost:8000
"""
import html
import re
import sys
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

import erp

PORT = 8000


# ---------------------------------------------------------------- helpers
def esc(x):
    return html.escape("" if x is None else str(x))


def money(x):
    return f"{x:,.0f}"


def to_int(value, label):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"Please enter a whole number for {label}.")


def to_float(value, label):
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Please enter a number for {label}.")


CSS = """
:root,[data-theme="fresh"]{--bg:#f0f8f6;--card:#ffffff;--ink:#16302b;--muted:#587770;--line:#d6e8e3;
--brand:#0b8277;--ok:#0f7b45;--okbg:#ddf4e8;--warn:#a85a00;--warnbg:#fdeed2;--bad:#c0392b;--badbg:#fde6e3;
--field:#ffffff;--fieldline:#b3d3cc;--head:#0f766e;--headink:#d9f4ef;--headsec:#8ed3c8;--link:#0b7a70;
--secbtn:#5a7871;--dangerbtn:#d64545;--graybg:#e3eeeb;--graytxt:#46605a;--ph:#8aa59e;color-scheme:light}
[data-theme="sunny"]{--bg:#fff8ee;--card:#ffffff;--ink:#3a2a14;--muted:#8a7050;--line:#f1e1c6;
--brand:#c75f00;--ok:#2f7d32;--okbg:#e4f3df;--warn:#a85a00;--warnbg:#ffecc9;--bad:#c0392b;--badbg:#fde6e3;
--field:#ffffff;--fieldline:#e6cfa8;--head:#d9730d;--headink:#fff0dc;--headsec:#ffd29c;--link:#b45309;
--secbtn:#8a7050;--dangerbtn:#d64545;--graybg:#f4ead7;--graytxt:#6d573a;--ph:#b39a76;color-scheme:light}
[data-theme="sky"]{--bg:#eef5ff;--card:#ffffff;--ink:#14263f;--muted:#587090;--line:#d6e3f7;
--brand:#2563eb;--ok:#0f7b45;--okbg:#ddf4e8;--warn:#a85a00;--warnbg:#fdeed2;--bad:#c0392b;--badbg:#fde6e3;
--field:#ffffff;--fieldline:#b8cdee;--head:#1d4ed8;--headink:#dbe8ff;--headsec:#9db9f2;--link:#1d4ed8;
--secbtn:#587090;--dangerbtn:#d64545;--graybg:#e5edf9;--graytxt:#46597a;--ph:#8da2c4;color-scheme:light}
[data-theme="dark"]{--bg:#0e1320;--card:#172033;--ink:#e8ecf5;--muted:#8d98b0;--line:#2a3550;
--brand:#3a62d6;--ok:#4ade9f;--okbg:rgba(74,222,159,.15);--warn:#fbbf5c;--warnbg:rgba(251,191,92,.15);
--bad:#ff7070;--badbg:rgba(255,112,112,.15);--field:#0e1320;--fieldline:#3a4766;--head:#090d17;
--headink:#aab6d3;--headsec:#5f6d92;--link:#7fa0ff;--secbtn:#3a4766;--dangerbtn:#c23b3b;
--graybg:#2a3550;--graytxt:#b6c0d8;--ph:#66728f;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;font-family:Segoe UI,Roboto,Arial,sans-serif;background:var(--bg);color:var(--ink);font-size:15px}
header{background:var(--head);padding:0 24px}
header .in{max-width:1100px;margin:auto;display:flex;align-items:center;gap:22px;flex-wrap:wrap}
header h1{font-size:18px;margin:0;padding:16px 0;color:#fff}
nav a{color:var(--headink);text-decoration:none;padding:18px 4px;display:inline-block;margin-right:14px;opacity:.92}
nav a:hover{opacity:1;text-decoration:underline}
nav .sec{color:var(--headsec);font-size:11px;text-transform:uppercase;letter-spacing:.06em;margin-right:6px}
.themes{margin-left:auto;display:flex;align-items:center;gap:6px;color:var(--headink);font-size:13px}
.themes select{padding:4px 6px;font-size:13px}
main{max-width:1100px;margin:24px auto;padding:0 24px 60px}
h2{margin:0 0 14px;font-size:20px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px;margin-bottom:20px;box-shadow:0 1px 2px rgba(0,0,0,.04)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin-bottom:20px}
.stat{background:var(--card);border:1px solid var(--line);border-top:4px solid var(--brand);border-radius:12px;padding:16px}
.stat .n{font-size:26px;font-weight:600}.stat .l{color:var(--muted);font-size:13px}
table{width:100%;border-collapse:collapse}
th,td{text-align:left;padding:9px 8px;border-bottom:1px solid var(--line);vertical-align:middle}
th{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}
td.r,th.r{text-align:right}
input,select{padding:7px 9px;border:1px solid var(--fieldline);border-radius:6px;font-size:14px;background:var(--field);color:var(--ink)}
input::placeholder{color:var(--ph)}
input:focus,select:focus{outline:2px solid var(--brand);outline-offset:0}
input[type=number]{width:90px}
input.w{width:150px}
button{padding:7px 13px;border:0;border-radius:6px;background:var(--brand);color:#fff;font-size:14px;cursor:pointer}
button:hover{filter:brightness(1.12)}
button.sec{background:var(--secbtn)}button.danger{background:var(--dangerbtn)}
form.inline{display:inline-flex;gap:6px;align-items:center;flex-wrap:wrap;margin:2px 0}
.msg{padding:11px 14px;border-radius:8px;margin-bottom:18px}
.ok{background:var(--okbg);color:var(--ok)}
.err{background:var(--badbg);color:var(--bad)}
.badge{padding:2px 9px;border-radius:99px;font-size:12px;font-weight:600}
.b-ok{background:var(--okbg);color:var(--ok)}.b-warn{background:var(--warnbg);color:var(--warn)}
.b-bad{background:var(--badbg);color:var(--bad)}.b-gray{background:var(--graybg);color:var(--graytxt)}
.muted{color:var(--muted)}a{color:var(--link)}
.note{font-size:13px;color:var(--muted);margin-top:8px}
"""

NAV = [
    ("Dashboard", "/"),
    ("INVENTORY", None), ("Products", "/products"),
    ("SALES", None), ("Customers", "/customers"), ("Orders", "/orders"), ("New order", "/orders/new"),
    ("FINANCE", None), ("Invoices", "/invoices"),
]


THEME_PICKER = """<div class="themes"><label for="theme">Theme</label>
<select id="theme" onchange="try{localStorage.setItem('erpTheme',this.value)}catch(e){}document.documentElement.setAttribute('data-theme',this.value)">
<option value="fresh">Fresh (teal)</option><option value="sunny">Sunny (orange)</option>
<option value="sky">Sky (blue)</option><option value="dark">Dark</option></select></div>
<script>try{var _t=localStorage.getItem('erpTheme');if(_t)document.getElementById('theme').value=_t}catch(e){}</script>"""


def page(title, body, msg=None, err=None):
    nav = ""
    for label, href in NAV:
        nav += (f'<a href="{href}">{label}</a>' if href
                else f'<span class="sec">{label}</span>')
    banner = ""
    if msg:
        banner += f'<div class="msg ok">{esc(msg)}</div>'
    if err:
        banner += f'<div class="msg err">{esc(err)}</div>'
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} - Retail ERP</title><style>{CSS}</style>
<script>try{{var t=localStorage.getItem("erpTheme");if(t)document.documentElement.setAttribute("data-theme",t)}}catch(e){{}}</script></head><body>
<header><div class="in"><h1>Retail ERP</h1><nav>{nav}</nav>{THEME_PICKER}</div></header>
<main>{banner}{body}</main></body></html>"""


def badge(status):
    cls = {"PAID": "b-ok", "CONFIRMED": "b-ok", "PARTIAL": "b-warn", "UNPAID": "b-warn",
           "CANCELLED": "b-bad", "VOID": "b-bad"}.get(status, "b-gray")
    return f'<span class="badge {cls}">{esc(status)}</span>'


# ------------------------------------------------------------------ pages
def page_dashboard(conn):
    s = erp.sales_summary(conn)
    low = erp.low_stock(conn)
    products = len(erp.list_products(conn))
    stat = lambda n, l: f'<div class="stat"><div class="n">{n}</div><div class="l">{l}</div></div>'
    body = "<h2>Dashboard</h2><div class=grid>"
    body += stat(s["orders"], "Confirmed orders")
    body += stat(money(s["revenue"]), "Total revenue")
    body += stat(money(erp.outstanding_receivables(conn)), "Money still owed (receivables)")
    body += stat(products, "Products")
    body += stat(len(low), "Products low on stock")
    body += "</div>"
    body += '<div class="card"><h2>Low stock alerts</h2>'
    if low:
        body += "<table><tr><th>Product</th><th class=r>In stock</th><th class=r>Reorder at</th></tr>"
        for p in low:
            body += (f"<tr><td>{esc(p['name'])}</td><td class=r>{p['stock_qty']}</td>"
                     f"<td class=r>{p['reorder_level']}</td></tr>")
        body += "</table>"
    else:
        body += '<p class="muted">Nothing is below its reorder level.</p>'
    body += "</div>"
    body += ('<div class="card"><h2>How the modules connect</h2><p class="muted">Placing an order '
             "(Sales) reduces stock (Inventory) and creates an invoice (Finance) in one database "
             "transaction. If any step fails, none of it is saved.</p></div>")
    return page("Dashboard", body)


def page_products(conn, msg, err):
    body = "<h2>Products (Inventory)</h2>"
    body += """<div class="card"><h3 style="margin-top:0">Add product</h3>
<form class="inline" method="post" action="/products/add">
<input class="w" name="sku" placeholder="SKU e.g. TEA-250" required>
<input class="w" name="name" placeholder="Name" required>
<input type="number" step="any" name="price" placeholder="Price" required>
<input type="number" name="stock" placeholder="Opening stock" style="width:130px" required>
<input type="number" name="reorder" placeholder="Reorder level (default 5)" style="width:190px">
<button>Add</button></form></div>"""
    body += '<div class="card"><table><tr><th>ID</th><th>SKU</th><th>Edit name / price / reorder level</th>'
    body += "<th class=r>Stock</th><th>Restock</th><th></th></tr>"
    for p in erp.list_products(conn):
        low = ' <span class="badge b-bad">LOW</span>' if p["stock_qty"] <= p["reorder_level"] else ""
        body += f"""<tr><td>{p['product_id']}</td><td>{esc(p['sku'])}</td>
<td><form class="inline" method="post" action="/products/update">
<input type="hidden" name="id" value="{p['product_id']}">
<input class="w" name="name" value="{esc(p['name'])}">
<input type="number" step="any" name="price" value="{p['unit_price']:.0f}">
<input type="number" name="reorder" value="{p['reorder_level']}">
<button class="sec">Save</button></form></td>
<td class=r>{p['stock_qty']}{low}</td>
<td><form class="inline" method="post" action="/products/restock">
<input type="hidden" name="id" value="{p['product_id']}">
<input type="number" name="qty" placeholder="Qty" required><button>Add stock</button></form></td>
<td><a href="/products/{p['product_id']}/history">History</a>
<form class="inline" method="post" action="/products/delete"
 onsubmit="return confirm('Delete this product?')">
<input type="hidden" name="id" value="{p['product_id']}"><button class="danger">Delete</button></form></td></tr>"""
    body += "</table></div>"
    return page("Products", body, msg, err)


def page_stock_history(conn, pid):
    p = conn.execute("SELECT * FROM products WHERE product_id=?", (pid,)).fetchone()
    if not p:
        return page("Not found", "<h2>Product not found</h2>")
    body = f"<h2>Stock history: {esc(p['name'])}</h2><p>Current stock: <b>{p['stock_qty']}</b></p>"
    body += '<div class="card"><table><tr><th>When</th><th class=r>Change</th><th>Reason</th><th>Order</th></tr>'
    for m in erp.stock_history(conn, pid):
        link = f'<a href="/orders/{m["order_id"]}">#{m["order_id"]}</a>' if m["order_id"] else ""
        body += (f"<tr><td>{esc(m['moved_at'])}</td><td class=r>{m['change_qty']:+d}</td>"
                 f"<td>{esc(m['reason'])}</td><td>{link}</td></tr>")
    body += '</table><p class="note">Stock on hand always equals the sum of these movements.</p></div>'
    body += '<p><a href="/products">&larr; Back to products</a></p>'
    return page("Stock history", body)


def page_customers(conn, msg, err):
    body = "<h2>Customers (Sales)</h2>"
    body += """<div class="card"><h3 style="margin-top:0">Add customer</h3>
<form class="inline" method="post" action="/customers/add">
<input class="w" name="name" placeholder="Name" required>
<input class="w" name="phone" placeholder="Phone (unique)" required>
<input class="w" name="email" placeholder="Email (optional)">
<button>Add</button></form></div>"""
    body += '<div class="card"><table><tr><th>ID</th><th>Edit name / phone / email</th><th></th></tr>'
    for c in erp.list_customers(conn):
        body += f"""<tr><td>{c['customer_id']}</td><td>
<form class="inline" method="post" action="/customers/update">
<input type="hidden" name="id" value="{c['customer_id']}">
<input class="w" name="name" value="{esc(c['name'])}">
<input class="w" name="phone" value="{esc(c['phone'])}">
<input class="w" name="email" value="{esc(c['email'])}">
<button class="sec">Save</button></form></td><td>
<form class="inline" method="post" action="/customers/delete"
 onsubmit="return confirm('Delete this customer?')">
<input type="hidden" name="id" value="{c['customer_id']}"><button class="danger">Delete</button></form></td></tr>"""
    body += "</table></div>"
    return page("Customers", body, msg, err)


def page_orders(conn, msg, err):
    body = '<h2>Orders (Sales)</h2><p><a href="/orders/new"><button>+ New order</button></a></p>'
    body += ('<div class="card"><table><tr><th>Order</th><th>Customer</th><th>Date</th><th>Status</th>'
             "<th class=r>Total</th><th>Invoice</th><th></th></tr>")
    for o in erp.list_orders(conn):
        cancel = ""
        if o["status"] == "CONFIRMED":
            cancel = (f'<form class="inline" method="post" action="/orders/cancel" '
                      f"onsubmit=\"return confirm('Cancel this order? Stock will be returned.')\">"
                      f'<input type="hidden" name="id" value="{o["order_id"]}">'
                      f'<button class="danger">Cancel</button></form>')
        body += (f"<tr><td><a href=\"/orders/{o['order_id']}\">#{o['order_id']}</a></td>"
                 f"<td>{esc(o['customer'])}</td><td>{esc(o['order_date'])}</td><td>{badge(o['status'])}</td>"
                 f"<td class=r>{money(o['total_amount'])}</td>"
                 f"<td>#{o['invoice_id']} {badge(o['invoice_status'])}</td><td>{cancel}</td></tr>")
    body += "</table></div>"
    return page("Orders", body, msg, err)


def page_new_order(conn, msg, err):
    customers = erp.list_customers(conn)
    opts = "".join(f'<option value="{c["customer_id"]}">{esc(c["name"])} ({esc(c["phone"])})</option>'
                   for c in customers)
    body = "<h2>New order</h2>"
    body += f'<form method="post" action="/orders/place"><div class="card">'
    body += f'<p><b>Customer:</b> <select name="customer_id" required>{opts}</select></p>'
    body += ('<table><tr><th>Product</th><th class=r>Price</th><th class=r>In stock</th>'
             "<th>Quantity</th></tr>")
    for p in erp.list_products(conn):
        body += (f"<tr><td>{esc(p['name'])}</td><td class=r>{money(p['unit_price'])}</td>"
                 f"<td class=r>{p['stock_qty']}</td>"
                 f'<td><input type="number" min="0" value="0" name="qty_{p["product_id"]}"></td></tr>')
    body += "</table>"
    body += ('<p class="note">Enter a quantity for each product you are selling. On submit, stock is reduced '
             "and an invoice is created automatically.</p>")
    body += "<p><button>Place order</button></p></div></form>"
    return page("New order", body, msg, err)


def page_order_detail(conn, oid):
    o = conn.execute("SELECT o.*, c.name AS customer FROM sales_orders o "
                     "JOIN customers c ON c.customer_id=o.customer_id WHERE order_id=?", (oid,)).fetchone()
    if not o:
        return page("Not found", "<h2>Order not found</h2>")
    inv = conn.execute("SELECT * FROM invoices WHERE order_id=?", (oid,)).fetchone()
    body = f"<h2>Order #{o['order_id']} {badge(o['status'])}</h2>"
    body += f"<p>Customer: <b>{esc(o['customer'])}</b> &middot; {esc(o['order_date'])}</p>"
    body += '<div class="card"><table><tr><th>Product</th><th class=r>Qty</th><th class=r>Price</th><th class=r>Line total</th></tr>'
    for r in erp.order_detail(conn, oid):
        body += (f"<tr><td>{esc(r['name'])}</td><td class=r>{r['quantity']}</td>"
                 f"<td class=r>{money(r['unit_price'])}</td><td class=r>{money(r['line_total'])}</td></tr>")
    body += f"<tr><td colspan=3 class=r><b>Total</b></td><td class=r><b>{money(o['total_amount'])}</b></td></tr></table>"
    if inv:
        body += f'<p>Invoice #{inv["invoice_id"]}: {badge(inv["status"])} &middot; <a href="/invoices">view invoices</a></p>'
    body += '</div><p><a href="/orders">&larr; Back to orders</a></p>'
    return page("Order", body)


def page_invoices(conn, msg, err):
    body = "<h2>Invoices &amp; payments (Finance)</h2>"
    body += ('<div class="card"><table><tr><th>Invoice</th><th>Order</th><th>Customer</th>'
             "<th class=r>Due</th><th class=r>Paid</th><th class=r>Balance</th><th>Status</th><th>Record payment</th></tr>")
    for i in erp.list_invoices(conn):
        # a voided invoice owes nothing, even though its original amount is kept for the record
        balance = 0 if i["status"] == "VOID" else i["amount_due"] - i["paid"]
        pay = ""
        if i["status"] in ("UNPAID", "PARTIAL"):
            pay = (f'<form class="inline" method="post" action="/payments/add">'
                   f'<input type="hidden" name="invoice_id" value="{i["invoice_id"]}">'
                   f'<input type="number" step="any" name="amount" value="{balance:.0f}" style="width:100px">'
                   f'<select name="method"><option>CASH</option><option>MOBILE_MONEY</option><option>CARD</option></select>'
                   f"<button>Pay</button></form>")
        body += (f"<tr><td>#{i['invoice_id']}</td><td><a href=\"/orders/{i['order_id']}\">#{i['order_id']}</a></td>"
                 f"<td>{esc(i['customer'])}</td><td class=r>{money(i['amount_due'])}</td>"
                 f"<td class=r>{money(i['paid'])}</td><td class=r>{money(balance)}</td>"
                 f"<td>{badge(i['status'])}</td><td>{pay}</td></tr>")
    body += "</table></div>"
    return page("Invoices", body, msg, err)


# --------------------------------------------------------------- routing
def handle_post(conn, path, f):
    """Return a success message. Raise ValueError for any business-rule problem."""
    if path == "/products/add":
        erp.add_product(conn, f("sku"), f("name"), to_float(f("price"), "price"),
                        to_int(f("stock"), "stock"), to_int(f("reorder") or "5", "reorder level"))
        return "/products", "Product added."
    if path == "/products/update":
        erp.update_product(conn, to_int(f("id"), "id"), f("name"),
                           to_float(f("price"), "price"), to_int(f("reorder"), "reorder level"))
        return "/products", "Product updated."
    if path == "/products/restock":
        erp.restock_product(conn, to_int(f("id"), "id"), to_int(f("qty"), "quantity"))
        return "/products", "Stock added and movement recorded."
    if path == "/products/delete":
        erp.delete_product(conn, to_int(f("id"), "id"))
        return "/products", "Product deleted."
    if path == "/customers/add":
        erp.add_customer(conn, f("name"), f("phone"), f("email") or None)
        return "/customers", "Customer added."
    if path == "/customers/update":
        erp.update_customer(conn, to_int(f("id"), "id"), f("name"), f("phone"), f("email"))
        return "/customers", "Customer updated."
    if path == "/customers/delete":
        erp.delete_customer(conn, to_int(f("id"), "id"))
        return "/customers", "Customer deleted."
    if path == "/orders/place":
        items = []
        for key in f.keys():
            m = re.fullmatch(r"qty_(\d+)", key)
            if m and f(key):
                qty = to_int(f(key), "quantity")
                if qty > 0:
                    items.append((int(m.group(1)), qty))
        order_id, total = erp.place_order(conn, to_int(f("customer_id"), "customer"), items)
        return f"/orders/{order_id}", (f"Order #{order_id} placed. Total {money(total)}. "
                                        "Stock reduced and invoice created automatically.")
    if path == "/orders/cancel":
        erp.cancel_order(conn, to_int(f("id"), "id"))
        return "/orders", "Order cancelled: stock returned and invoice voided."
    if path == "/payments/add":
        erp.record_payment(conn, to_int(f("invoice_id"), "invoice"),
                           to_float(f("amount"), "amount"), f("method"))
        return "/invoices", "Payment recorded."
    raise LookupError


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # keep the terminal quiet
        pass

    def send_html(self, content, status=200):
        data = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, location, msg=None, err=None):
        q = {}
        if msg:
            q["msg"] = msg
        if err:
            q["err"] = err
        if q:
            location += "?" + urllib.parse.urlencode(q)
        self.send_response(303)
        self.send_header("Location", location)
        self.end_headers()

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(url.query)
        msg, err = q.get("msg", [None])[0], q.get("err", [None])[0]
        path = url.path.rstrip("/") or "/"
        conn = erp.connect()
        try:
            if path == "/":
                out = page_dashboard(conn)
            elif path == "/products":
                out = page_products(conn, msg, err)
            elif re.fullmatch(r"/products/\d+/history", path):
                out = page_stock_history(conn, int(path.split("/")[2]))
            elif path == "/customers":
                out = page_customers(conn, msg, err)
            elif path == "/orders":
                out = page_orders(conn, msg, err)
            elif path == "/orders/new":
                out = page_new_order(conn, msg, err)
            elif re.fullmatch(r"/orders/\d+", path):
                out = page_order_detail(conn, int(path.split("/")[2]))
                if msg:  # show the success banner on the detail page too
                    out = out.replace("<main>", f'<main><div class="msg ok">{esc(msg)}</div>', 1)
            elif path == "/invoices":
                out = page_invoices(conn, msg, err)
            else:
                return self.send_html(page("Not found", "<h2>Page not found</h2>"), 404)
            self.send_html(out)
        finally:
            conn.close()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = urllib.parse.parse_qs(self.rfile.read(length).decode("utf-8"), keep_blank_values=True)

        class Form:
            def __call__(self, key):
                return raw.get(key, [""])[0].strip()

            def keys(self):
                return raw.keys()

        path = urllib.parse.urlparse(self.path).path
        conn = erp.connect()
        try:
            try:
                location, message = handle_post(conn, path, Form())
                self.redirect(location, msg=message)
            except ValueError as e:
                back = {"/orders/place": "/orders/new", "/orders/cancel": "/orders",
                        "/payments/add": "/invoices"}.get(
                    path, "/" + path.strip("/").split("/")[0])
                self.redirect(back, err=str(e))
            except LookupError:
                self.send_html(page("Not found", "<h2>Page not found</h2>"), 404)
        finally:
            conn.close()


def main():
    conn = erp.connect()
    erp.init_db(conn)
    if erp.seed_demo_data(conn):
        print("First run: sample products and customers loaded.")
    conn.close()
    try:
        server = HTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        print(f"Port {PORT} is busy. Close the other copy of web.py (Ctrl+C in its terminal) and try again.")
        sys.exit(1)
    url = f"http://localhost:{PORT}"
    print(f"Retail ERP is running at {url}")
    print("Press Ctrl+C in this terminal to stop it.")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
