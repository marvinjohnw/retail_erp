-- ============================================================
-- Retail ERP prototype: single integrated database schema
-- Modules sharing ONE database:
--   1. Inventory  (products, stock_movements)
--   2. Sales      (customers, sales_orders, order_items)
--   3. Finance    (invoices, payments)
-- ============================================================

PRAGMA foreign_keys = ON;   -- make SQLite actually enforce foreign keys

-- ---------- SALES MODULE ----------
CREATE TABLE IF NOT EXISTS customers (
    customer_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL CHECK (length(trim(name)) > 0),
    phone        TEXT NOT NULL UNIQUE,          -- UNIQUE stops duplicate customers
    email        TEXT
);

-- ---------- INVENTORY MODULE ----------
CREATE TABLE IF NOT EXISTS products (
    product_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    sku            TEXT NOT NULL UNIQUE,        -- stock code, can't be duplicated
    name           TEXT NOT NULL CHECK (length(trim(name)) > 0),
    unit_price     REAL NOT NULL CHECK (unit_price > 0),
    stock_qty      INTEGER NOT NULL DEFAULT 0 CHECK (stock_qty >= 0),  -- no negative stock
    reorder_level  INTEGER NOT NULL DEFAULT 5 CHECK (reorder_level >= 0)
);

-- ---------- SALES MODULE ----------
CREATE TABLE IF NOT EXISTS sales_orders (
    order_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id  INTEGER NOT NULL
                 REFERENCES customers(customer_id) ON DELETE RESTRICT,
    order_date   TEXT NOT NULL DEFAULT (datetime('now')),
    status       TEXT NOT NULL DEFAULT 'CONFIRMED'
                 CHECK (status IN ('CONFIRMED', 'CANCELLED')),
    total_amount REAL NOT NULL CHECK (total_amount >= 0)
);

CREATE TABLE IF NOT EXISTS order_items (
    item_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id     INTEGER NOT NULL
                 REFERENCES sales_orders(order_id) ON DELETE CASCADE,
    product_id   INTEGER NOT NULL
                 REFERENCES products(product_id) ON DELETE RESTRICT,
    quantity     INTEGER NOT NULL CHECK (quantity > 0),
    unit_price   REAL NOT NULL CHECK (unit_price > 0),   -- price at time of sale
    UNIQUE (order_id, product_id)                        -- one line per product
);

-- ---------- INVENTORY MODULE (audit trail) ----------
CREATE TABLE IF NOT EXISTS stock_movements (
    movement_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id   INTEGER NOT NULL
                 REFERENCES products(product_id) ON DELETE RESTRICT,
    change_qty   INTEGER NOT NULL CHECK (change_qty <> 0),  -- + in, - out
    reason       TEXT NOT NULL
                 CHECK (reason IN ('RESTOCK', 'SALE', 'CANCEL_RETURN', 'ADJUSTMENT')),
    order_id     INTEGER REFERENCES sales_orders(order_id) ON DELETE SET NULL,
    moved_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------- FINANCE MODULE ----------
CREATE TABLE IF NOT EXISTS invoices (
    invoice_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id     INTEGER NOT NULL UNIQUE      -- exactly one invoice per order
                 REFERENCES sales_orders(order_id) ON DELETE CASCADE,
    amount_due   REAL NOT NULL CHECK (amount_due >= 0),
    status       TEXT NOT NULL DEFAULT 'UNPAID'
                 CHECK (status IN ('UNPAID', 'PARTIAL', 'PAID', 'VOID')),
    issued_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id   INTEGER NOT NULL
                 REFERENCES invoices(invoice_id) ON DELETE RESTRICT,
    amount       REAL NOT NULL CHECK (amount > 0),
    method       TEXT NOT NULL CHECK (method IN ('CASH', 'MOBILE_MONEY', 'CARD')),
    paid_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
