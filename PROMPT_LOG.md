# AI Support Statement & Prompt Log

**Student:** [YOUR NAME / ID]  **Course:** ERP  **Date:** 10 Oct 2026
**AI tool used:** Claude (Anthropic), via a chat/coding assistant.

## AI Support Statement
I used a generative AI assistant to help me understand the assignment brief, plan the project, generate the
database schema and Python code, and write automated tests. The AI did not write my final reflection;
that is written by me. I ran the program, tested the demo flow myself, and I can explain the schema and code.
The areas below record where the AI was wrong or weak and how that was found and fixed.

## Prompt log

| # | My prompt (summary) | What the AI did | My action / evaluation |
|---|---|---|---|
| 1 | Uploaded the midterm brief: "I have failed to understand, break it down and tell me how we are going to do this." | Summarised the four deliverables, defined terms (ERP, module, single source of truth, CRUD, constraints, BPR) and proposed a plan. | [Write what you checked against the brief] |
| 2 | Asked what the "prompt" requirement meant, whether screenshots are needed, and Code::Blocks vs VS Code. | Explained the log is a record of prompts, that the brief asks for runnable code (screenshots only as support), and that Code::Blocks targets C/C++ so VS Code + Python is simpler. | [Note if you confirmed submission format with the lecturer] |
| 3 | Questioned why a retail shop was chosen ("I did not pick up on that anywhere"). | Admitted retail was only one of the brief's examples and was the AI's own suggestion, not a requirement. | I accepted retail because the Sales → Stock → Invoice flow is easy to demonstrate. |
| 4 | "Go ahead with retail." Asked the AI to build the prototype. | Generated `schema.sql`, `erp.py`, `app.py`, `test_erp.py`, and documentation. | [Write that you installed Python, ran the program and the demo flow] |

## Errors, weaknesses and limitations found in the AI's work

1. **Seed data broke the audit trail.** The AI's first version of the sample-data loader inserted opening
   stock directly without writing `stock_movements` rows. That meant `stock_qty` would never equal the sum
   of the movement history, which is a data-consistency flaw in a system meant to have a single source of truth.
   *Found when:* the AI wrote a reconciliation test and noticed it could not meaningfully pass. *Fix:* seed data
   now logs an opening `RESTOCK` movement for every product.
2. **A weak test.** The first "consistency" test computed the movement total but never compared it to anything
   (it only asserted stock was non-negative), so it passed while proving nothing. It was rewritten to assert
   `stock_qty == SUM(change_qty)` for every product.
3. **Tooling mistake in running tests.** The AI ran Python with the `-I` (isolated) flag, which caused
   `ModuleNotFoundError: No module named 'erp'`. This was a mistake in the command, not in the code; re-running
   normally worked. A reminder that AI-generated commands also need checking.
4. **Money stored as floating point (`REAL`).** This is poor practice for financial data because of rounding
   error; the code works around it with a small tolerance when comparing amounts. For a production system the
   AI's design should use integer amounts or `DECIMAL`. It is listed as a known limitation.
5. **Missing real-world enterprise logic.** The AI did not include user roles/login, tax, discounts, suppliers or
   purchase orders, refunds for cancelling a paid order (the system simply refuses), concurrent users, or backups.
   These are things a real ERP such as SAP or Odoo handles and a prompt-driven prototype does not.
6. **A recommendation presented as if it were a requirement.** The AI first proposed a retail shop without
   making clear this was its own choice; I had to question it (prompt 3).

7. **Changed the interface plan without telling me.** The AI's original plan said "Flask web dashboard", then it
   built a terminal-only menu without saying so, to avoid installation risk. I only noticed when I ran it in VS Code
   and expected a website. The AI admitted this and then built `web.py`, a website using only Python's standard
   library. *Lesson:* check that what an AI delivers matches what it said it would deliver.
8. **A bug the AI introduced and caught in testing.** In the first draft of `web.py`, a failed payment redirected
   to a page that does not exist (`/payments`). Found by sending a bad payment during automated testing; fixed to
   redirect to `/invoices`.
9. **The AI's own test command killed itself.** A cleanup command (`pkill -f web.py`) matched its own shell and
   stopped the test run (exit code 144). Re-run in separate steps.

10. **A display bug found only by looking at the screen.** After a dark-theme change, a screenshot showed a voided
    (cancelled) invoice with a balance of 7,500, as if the customer still owed it. The database and the summary
    report were correct; only the invoice table's balance column was wrong. Automated tests had not caught it
    because they checked data, not what the page displays. Fixed so VOID invoices show a balance of 0.

## Verification I did myself
- [Ran `python test_erp.py` and saw ALL TESTS PASSED: add date/time]
- [Ran the demo flow in README: placed an order, saw stock fall and invoice appear]
- [Tried to break it: ordering more than stock, duplicate phone number, deleting a product with sales]
- [Anything you changed in the code or schema, and why]

## Further prompts (add every new AI question you ask, in the same format)
| # | My prompt | AI response summary | My evaluation |
|---|---|---|---|
| 5 | Asked why I had no website, then said I was upset. | Admitted the interface change, built `web.py` (dashboard, products, customers, orders, invoices, payments), tested all pages and error cases, and took screenshots to check the layout. | [Write what you checked on the website] |
| 6 | Asked to discuss colours; chose dark mode; then said it was too dark and wanted lighter, brighter colours. | Applied dark theme, then added a light theme set with an in-page theme switcher (Fresh, Sunny, Sky, Dark). | I compared the themes by looking at screenshots and chose [your choice]. |
| 7 | | | |
