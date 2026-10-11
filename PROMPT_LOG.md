# AI Support Statement and Prompt Log

**Student:** YOUR NAME AND STUDENT NUMBER
**Course:** Enterprise Resource Planning (ERP) Midterm Project
**AI tool used:** Claude (Anthropic)

## AI Support Statement

I used a generative AI assistant to help me understand the assignment brief, plan the project, and generate the
database schema, the Python code and the automated tests. The AI did not write my final reflection; I wrote
that myself. I installed Python, ran the program on my own computer, ran the tests, and used the system to place
orders, record payments and check that stock and invoices updated. I can explain how the database and the main
order process work.

## Prompt log

### 1. Understanding the assignment
- **What I asked:** I uploaded the midterm brief and said I did not understand it. I asked for it to be broken
  down and for a plan.
- **What the AI did:** Explained the four deliverables and the key terms (ERP, module, single source of truth,
  CRUD, constraints, BPR), and suggested a plan.
- **My check:** I compared the explanation with the original brief.

### 2. Questions about the requirements and tools
- **What I asked:** What the "prompt log" means, whether screenshots are needed, and whether to use Code::Blocks
  or VS Code.
- **What the AI did:** Explained that the log is a record of my AI prompts, that the brief asks for runnable code,
  and that VS Code with Python is simpler than Code::Blocks (which is mainly for C/C++).

### 3. Choosing the organization
- **What I asked:** Why a retail shop was chosen, because I could not find it in the brief.
- **What the AI did:** Admitted that retail was only one of the brief's examples and was its own suggestion,
  not a requirement.
- **My decision:** I accepted a retail shop because the flow from sale to stock to invoice is easy to show.

### 4. Building the prototype
- **What I asked:** To go ahead and build the prototype.
- **What the AI did:** Generated the database schema (`schema.sql`), the business logic (`erp.py`), a terminal
  menu (`app.py`), automated tests (`test_erp.py`) and the documentation.

### 5. Installing Python and running the project
- **What I asked:** Step-by-step help to unzip the files, install Python and run the project in VS Code.
- **What happened:** Python was not installed ("Python was not found"). The installer on my computer used the
  `py` command instead of `python`. The AI guided me through installing it, and the tests then passed on my
  own computer.

### 6. Asking for a website
- **What I asked:** Why I had a terminal menu and not a website.
- **What the AI did:** Admitted it had changed the plan without telling me, then built a web version (`web.py`)
  using only Python's standard library, on the same database and rules.

### 7. Colours and themes
- **What I asked:** To change the colours. I first chose dark mode, then asked for lighter, brighter colours.
- **What the AI did:** Added a theme switcher with four themes (Fresh, Sunny, Sky, Dark). I chose the
  theme I preferred by looking at them.

### 8. Putting the project on GitHub
- **What I asked:** How to upload my project to GitHub.
- **What the AI did:** Gave me step-by-step instructions, which I followed to create the repository and upload
  my files.

## Errors, weaknesses and limitations in the AI's work

1. **Sample data broke the stock audit trail.** The first version of the sample-data loader added opening stock
   without recording a stock movement, so stock levels could not be reconciled with the movement history.
   *Found by:* writing a proper reconciliation test. *Fixed:* opening stock is now recorded as a movement.
2. **A test that proved nothing.** The first consistency test did not compare the numbers it calculated. It was
   rewritten to check that stock on hand equals the sum of all stock movements for every product.
3. **A wrong command.** The AI ran Python with a flag that stopped it finding its own files
   (`ModuleNotFoundError`). The code was fine; the command was wrong. AI-written commands also need checking.
4. **Money stored as decimals that can round badly (`REAL`).** This is poor practice for financial data. A
   production system should store whole numbers or use an exact decimal type. It is listed as a known limitation.
5. **Missing real-world business logic.** The AI did not include user login and roles, tax, discounts, suppliers,
   purchase orders, refunds for paid orders (the system only refuses to cancel them), several users at once, or
   backups. A real ERP such as SAP or Odoo handles these.
6. **A suggestion presented like a requirement.** The AI proposed a retail shop without saying it was only
   its own choice. I had to question it (entry 3).
7. **A plan changed without telling me.** The AI said it would build a web dashboard, then built a terminal
   menu and did not say so. I only noticed when I ran it. Lesson: check that what the AI delivers matches
   what it said it would deliver.
8. **A bug in the first website version.** A failed payment sent the user to a page that does not exist.
   Found while testing a bad payment, and fixed.
9. **A display bug the tests could not see.** A cancelled order's invoice still showed an amount owed on screen,
   although the database and summary report were correct. Found by looking at a screenshot of the page, because
   the automated tests checked data and not the screen. Fixed so cancelled invoices show a balance of 0.

## What I verified myself
- I ran the automated tests on my own computer and they all passed.
- I ran the website, placed an order, and saw the stock go down and an invoice appear.
- I took screenshots of the main steps (they are in the `screenshots erp` folder in the repository).
- I uploaded the project to GitHub and checked that the files and README display correctly.
- My own changes to the code or design: ADD ANYTHING YOU CHANGED, OR DELETE THIS LINE.
