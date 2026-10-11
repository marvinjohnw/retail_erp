# Retail ERP Prototype (Inventory + Sales + Finance)

A small ERP for a retail shop, with a web dashboard and a terminal menu. Three modules (Inventory, Sales and Finance) share one SQLite database.

## Files
| File | Purpose |
|---|---|
| `schema.sql` | Database structure (DDL) with all constraints |
| `erp.py` | Business logic (CRUD + the order → stock → invoice transaction) |
| `web.py` | **The website version (recommended for demo)** |
| `app.py` | The terminal menu version (same database and logic) |
| `test_erp.py` | Automated checks |
| `ARCHITECTURE.md` | ER diagram, data flow, validation rules, limitations |
| `PROMPT_LOG.md` | AI Support Statement and prompt log |

## Setup (Windows, VS Code)
1. Install Python from https://www.python.org/downloads/ . **Tick "Add python.exe to PATH"** on the first installer screen.
2. Open VS Code → **File → Open Folder** → choose this folder.
3. Open the terminal: **Terminal → New Terminal**.
4. Check Python works: `python --version` (on some machines the command is `py`).
5. No extra libraries are needed. Everything used comes with Python.

## Run the website (recommended)
```
py web.py
```
Your browser opens at http://localhost:8000. Use the menu at the top: Dashboard, Products, Customers,
Orders, New order, Invoices. Press **Ctrl+C** in the terminal to stop it.
(Use `python` instead of `py` if that is what works on your computer.)

## Or run the terminal version
```
py app.py
```
On first run the database `retail_erp.db` is created and sample data is loaded.
To start fresh, close the program and delete `retail_erp.db`.

## Test
```
python test_erp.py
```
You should see `ALL TESTS PASSED`.

## Try this demo flow
(Terminal menu numbers shown. On the website, use the matching pages.)
1. Menu **1**: view products (note Rice stock).
2. Menu **11**: place an order for customer 1 (e.g. product 1, qty 2).
3. Menu **1** again: stock has dropped. Menu **15**: an invoice exists automatically.
4. Menu **16**: record a payment. Menu **17**: see the summary report.
5. Menu **11** asking for more stock than exists: the order is rejected and nothing changes.
6. Menu **14**: cancel an unpaid order and see stock return and the invoice become VOID.
