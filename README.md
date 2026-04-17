# BHC Quotation Generator — v I.05

**TÜV Rheinland (India) Pvt. Ltd.**  
Building Health Check-Up (BHC) — Quotation Management System

An internal web application that manages the full lifecycle of BHC enquiries: from pulling raw Microsoft Forms data, generating professional PDF quotations, tracking workflow status, managing payments, to exporting reports — all through a clean browser UI with no external cloud dependency.

---

## Table of Contents

1. [What This Tool Does](#1-what-this-tool-does)
2. [User Guide — Full Feature Walkthrough](#2-user-guide--full-feature-walkthrough)
   - [Logging In](#21-logging-in)
   - [Dashboard](#22-dashboard)
   - [Working with Clients](#23-working-with-clients)
   - [Generating a Quotation PDF](#24-generating-a-quotation-pdf)
   - [Updating Status and Payments](#25-updating-status-and-payments)
   - [Exporting Data](#26-exporting-data)
   - [Admin Panel](#27-admin-panel)
3. [Developer Guide — Setup to Contribution](#3-developer-guide--setup-to-contribution)
   - [Prerequisites](#31-prerequisites)
   - [First-Time Setup](#32-first-time-setup)
   - [Configure Environment](#33-configure-environment)
   - [Run the Application](#34-run-the-application)
   - [Project Structure Explained](#35-project-structure-explained)
   - [How Data Flows Through the App](#36-how-data-flows-through-the-app)
   - [Database Design](#37-database-design)
   - [API Reference](#38-api-reference)
   - [Running Tests](#39-running-tests)
   - [Common Development Tasks](#310-common-development-tasks)
   - [Debugging Tips](#311-debugging-tips)
   - [Contributing a Fix or Feature](#312-contributing-a-fix-or-feature)
4. [Security Notes](#4-security-notes)
5. [Known Limitations](#5-known-limitations)
6. [Changelog](#6-changelog)

---

## 1. What This Tool Does

The BHC Quotation Generator is an internal tool built for the TÜV Rheinland India civil engineering team. Here is the complete workflow it supports:

```
Microsoft Forms enquiry
        ↓
Excel workbook (OneDrive / local)
        ↓
BHC Tool — reads pending clients
        ↓
Engineer reviews details, generates PDF quotation
        ↓
Status updated: Quoted → Converted / Dropped
        ↓
Payment tracking (Pending / Paid)
        ↓
Export to Excel / email draft
```

Everything is managed from one browser tab. No external cloud services are required at runtime.

---

## 2. User Guide — Full Feature Walkthrough

### 2.1 Logging In

1. Open **http://127.0.0.1:7860/bhc** in your browser.
2. Enter your **TÜV email** (must end with `@ind.tuv.com`) and password.
3. Click **Sign In**.

**First time on this system?**
- Click **Create Account** on the login screen.
- Fill in your name, email, and password. Choose a security question.
- Wait for an admin to approve your account. You will not be able to log in until approved.

**Forgot your password?**
- Click **Forgot Password** on the login screen.
- Enter your email. Answer your security question. Enter a new password.

**Must change password (first login):**
- If you see a "must change password" prompt after login, you are required to set a new password before accessing any feature.

---

### 2.2 Dashboard

After login you land on the **Dashboard** tab. It shows real-time summary cards:

| Card | What it shows |
|---|---|
| Pending Enquiries | Clients in the Excel sheet not yet quoted |
| Quoted | Clients who have received a quotation |
| Converted | Quotations accepted; projects in progress |
| Dropped | Leads that did not convert |
| Revenue Quoted | Total quoted value across all clients |
| Revenue Converted | Confirmed revenue (converted clients) |

The dashboard reads directly from the live Excel source. Click **Refresh** to pull the latest data at any time.

**Excel source indicator** — At the top of the dashboard there is a green/red status chip showing whether the Excel workbook is reachable. If red, check the data source path in the Admin Panel or upload a local Excel file.

---

### 2.3 Working with Clients

The **Clients** tab shows all enquiries. Use the search box and filters to narrow down:

- **Search** — by client name, email, city, or property name
- **Status filter** — Pending / Quoted / Converted / Dropped
- **Payment filter** — Pending / Paid
- **Property type filter** — Residential / Commercial / Industrial / etc.
- **Date range filter** — filter by enquiry date

**Client card** shows:
- Client name, email, phone
- Property name, city, area (sq.ft), structure type
- Current status badge and payment badge
- Quote reference number (once generated)

Click a client card to expand details and see all available actions.

---

### 2.4 Generating a Quotation PDF

1. Open a client from the **Clients** tab (Pending status).
2. Review the auto-calculated price shown on the card (based on area slabs).
3. Optionally **override the final price** manually.
4. Select **Structure Type**: RCC, Steel, or Both.
5. Click **Generate Quote**.

The system will:
- Assign a unique daily reference number (e.g. `BEN-HC-TUVR-20260417-0001`)
- Build the PDF using all sections configured in the Admin Panel
- Allow you to **Preview** the PDF in-browser before downloading
- Offer a **Download PDF** button
- Offer an **Email Draft** button (creates a `.eml` file you can open in Outlook)

**Quote reference numbers** reset their daily counter each new day and are stored permanently so they never repeat.

---

### 2.5 Updating Status and Payments

After generating and sending a quote, update the client's lifecycle status:

**Status transitions allowed:**

| From | To | Allowed? |
|---|---|---|
| Pending | Quoted | ✅ |
| Quoted | Converted | ✅ |
| Quoted | Dropped | ✅ |
| Converted | Dropped | ✅ |
| Any | Pending | ❌ (cannot go back) |

**Payment status:**

| Status | Payment allowed |
|---|---|
| Quoted | Pending only |
| Converted | Pending or Paid |
| Dropped | Pending only |

Use the **Update Status** form on any client card to change status and payment together.

---

### 2.6 Exporting Data

Go to the **Export** tab or use the **Export to Excel** button. Filters applied in the Clients view carry over to the export. The Excel export includes all client fields, status, payment, and quote reference.

**Email Draft** — available per client on the quotation generation screen. Downloads a `.eml` file with the client's email pre-filled, ready to open and send in Outlook.

---

### 2.7 Admin Panel

The Admin Panel is only visible to **admin accounts**. Access it from the top navigation bar.

#### Company Settings
Set the company name, address, contact details, and GST/surcharge percentages. These values appear on every generated quotation PDF.

#### Document Settings
Control what appears in the "About Us" and other standard sections of the PDF:
- Company profile paragraphs
- TÜV history paragraphs
- Service capabilities list
- Deliverables list
- Payment terms
- Other terms

#### Pricing Slabs
Configure the area-based pricing table for two categories:

- **Standard Building** (existing buildings, condition assessment)
- **New Building** (construction monitoring)

Each slab defines: minimum area, maximum area, label, and quoted price. The pricing engine picks the matching slab automatically based on the client's stated area.

You can:
- Edit any slab price directly in the table
- Add new slabs with the **+ Add Row** button
- Delete slabs with the trash icon

#### Scope of Work Templates
Pre-set the default scope text that appears in quotations, customized per structure type (RCC, Steel, Both) and per building category (Standard or New Building).

#### Support Documents Templates
Configure the list of documents required from the client for each structure type. This appears as a section in the quotation PDF.

#### Quotation Sections Manager *(New in v I.05)*
This is the most powerful customization feature. It controls **every section** of the generated PDF quotation.

**What you can do:**
- **Show / Hide** any section using the toggle switch — hidden sections are skipped in PDF generation
- **Reorder** sections by dragging the `≡` handle up or down — PDF order follows this order exactly
- **Edit** section heading and content directly inline (click **Edit** button)
- **Add a completely new custom section** using the **+ Add New Section** button:
  1. Enter a **Section Heading** (e.g. "Special Safety Conditions")
  2. Choose **Content Type**:
     - **Numbered List** — items rendered as 1., 2., 3...
     - **Paragraphs** — free-form text blocks
     - **Table** — task + duration two-column table
  3. Add content items using the interactive builder (one field per item, add/remove freely)
  4. Choose **Insert After** — where in the quotation this section should appear
  5. Click **Add Section**
- **Delete** any custom (non-system) section using the Delete button

System sections (marked with **System** badge) cannot be deleted but can be hidden and reordered.

**Important:** Click **Save Sections** to persist reorder changes. Individual toggle/edit/add/delete operations save immediately to the database.

#### User Management
- View all registered users and their approval status
- **Approve** pending registration requests
- **Create** a new user account directly (admin-created accounts require password change on first login)
- **Reset password** for any user

#### Audit Log
A read-only log of all security-relevant events:
- Login / logout
- Failed login attempts
- Password changes and resets
- Admin configuration changes
- Quotation section create / edit / delete

---

## 3. Developer Guide — Setup to Contribution

### 3.1 Prerequisites

Before you begin, make sure you have the following installed on your Windows machine:

| Requirement | Version | How to check |
|---|---|---|
| Python | 3.11 or 3.12 | `python --version` |
| pip | Latest | `pip --version` |
| Git | Any recent | `git --version` |
| PowerShell | 5.1+ | Comes with Windows 10/11 |

You do **not** need Node.js, Docker, or any other runtime. The frontend is plain HTML/CSS/JS.

---

### 3.2 First-Time Setup

Open PowerShell and run each step:

**Step 1 — Clone the repository**
```powershell
git clone https://github.com/NaveenkumarTUV/BHC_I.05.git
cd BHC_I.05
```

**Step 2 — Create a virtual environment**
```powershell
python -m venv .venv
```

**Step 3 — Activate the virtual environment**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```
> You must activate the venv every time you open a new PowerShell window. Your prompt will show `(.venv)` when active.

**Step 4 — Install dependencies**
```powershell
pip install -r backend\requirements.txt
```

**Step 5 — Create the environment file**
```powershell
Copy-Item backend\.env.example .env
```

---

### 3.3 Configure Environment

Open `.env` in any text editor (Notepad, VS Code, etc.) and set the values:

```
# Path to the Microsoft Forms Excel source file
# Leave blank to use data/bhc_enquiries.xlsx as fallback
EXCEL_FILE_PATH=C:\path\to\your\enquiries.xlsx

# Leave all DB paths blank to auto-create SQLite files in data/
BHC_PROCESSED_DB_PATH=
BHC_CONFIG_DB_PATH=

# Server settings
SERVER_HOST=127.0.0.1
SERVER_PORT=7860
DEBUG_MODE=true
```

**Excel file lookup order** (the app tries these in order):
1. `EXCEL_FILE_PATH` from your `.env`
2. Known OneDrive form workbook filenames (configured internally)
3. `data/bhc_enquiries.xlsx` (local fallback)

If no Excel is found, the dashboard shows zero pending clients but the app still runs.

---

### 3.4 Run the Application

```powershell
# Make sure venv is active (you see (.venv) in prompt)
.\.venv\Scripts\Activate.ps1

# Start the server
uvicorn backend.app.main:app --host 127.0.0.1 --port 7860 --reload
```

Open your browser and go to:
- **App UI** → http://127.0.0.1:7860/bhc
- **API docs** → http://127.0.0.1:7860/docs *(auto-generated, useful for testing endpoints)*
- **Session check** → http://127.0.0.1:7860/api/session

The `--reload` flag means the server restarts automatically every time you save a Python file — very useful during development.

**Default admin login (first run):**
- Email: `M.naveenkumar@ind.tuv.com`
- Password: `ChangeThisAdmin123`
- You will be forced to change the password on first login.

---

### 3.5 Project Structure Explained

```
BHC_I.05/
│
├── .env                        ← Your local environment config (never commit this)
├── backend/
│   ├── .env.example            ← Template for .env — commit this, not .env
│   ├── requirements.txt        ← Python package list
│   └── app/
│       ├── main.py             ← FastAPI app factory, startup, middleware
│       ├── config.py           ← Reads all environment variables
│       ├── routes/
│       │   └── bhc_routes.py   ← ALL API endpoints (41 routes)
│       ├── services/
│       │   ├── bhc_config_db.py        ← Config SQLite: auth, pricing, settings, sections
│       │   ├── bhc_workflow_db.py      ← Workflow SQLite: processed clients
│       │   ├── bhc_workflow_service.py ← Excel reading, client merging logic
│       │   ├── bhc_pricing_engine.py   ← Area-slab price calculation
│       │   ├── bhc_output_generator.py ← PDF generation (fpdf)
│       │   ├── bhc_excel_reader.py     ← Raw Excel parsing (openpyxl)
│       │   └── bhc_admin_auth.py       ← Session helpers, auth decorators
│       └── utils/
│           └── paths.py        ← DATA_DIR, EXPORTS_DIR, FRONTEND_DIR
│
├── frontend/
│   └── bhc/
│       ├── index.html          ← Single-page application shell
│       ├── script.js           ← All UI logic (~2500 lines, vanilla JS)
│       └── style.css           ← All styling (~1500 lines)
│
├── data/
│   ├── exports/bhc/            ← Generated PDFs and email drafts saved here
│   └── assets/                 ← Static assets (logos etc.)
│
└── backend/tests/
    ├── test_config_db.py       ← DB init, company/document/pricing updates
    ├── test_dashboard_summary.py ← Revenue calculations, quote references
    ├── test_pricing_engine.py  ← Slab pricing, overrides, structure types
    ├── test_user_auth.py       ← Login, sessions, password change, reset
    └── test_workflow_rules.py  ← Status/payment combination validation
```

**Key rule:** The frontend (`index.html` / `script.js` / `style.css`) is **pure vanilla JS** — no build tools, no npm, no webpack. You edit the file and refresh the browser. That's it.

---

### 3.6 How Data Flows Through the App

Understanding this flow makes everything else make sense:

**On page load:**
1. Browser loads `index.html` → `script.js` calls `GET /api/session`
2. If authenticated → calls `GET /api/bhc/clients` (workflow clients), `GET /api/bhc/dashboard`
3. Admin users additionally load `GET /api/bhc/admin/config`

**On Generate Quote:**
1. `POST /api/bhc/generate-quote` with client data and price override
2. Backend: `bhc_pricing_engine.py` calculates price → `bhc_output_generator.py` calls `list_quotation_sections()` from DB → builds PDF using fpdf → saves to `data/exports/bhc/`
3. Frontend receives file path → shows preview/download buttons

**On Admin Config Save:**
1. Any `PUT /api/bhc/admin/company` or similar endpoint
2. Backend validates, writes to SQLite (`bhc_config.db`)
3. Frontend refreshes admin config from `GET /api/bhc/admin/config`

**Quotation Sections (new v I.05):**
1. `GET /api/bhc/admin/quotation-sections` → returns 14 default + any custom sections
2. Toggle/edit/reorder/add/delete via dedicated PUT/POST/DELETE endpoints
3. On next PDF generation, `bhc_output_generator.py` reads sections fresh from DB — all changes are reflected immediately

---

### 3.7 Database Design

The app uses **two SQLite databases** (auto-created on first run):

#### `bhc_config.db` — Configuration and Auth
| Table | What it stores |
|---|---|
| `config_meta` | Schema version, key-value config pairs |
| `pricing_slabs` | Area-based pricing (standard + new building) |
| `company_settings` | Company name, address, contact, GST% |
| `document_settings` | About Us, deliverables, payment terms, etc. |
| `scope_of_work` | Per-structure-type scope templates |
| `users` | User accounts, password hashes, approval status |
| `sessions` | Active login sessions (8-hour TTL) |
| `audit_events` | Security audit trail |
| `quotation_sections` | All PDF sections: system defaults + custom |

#### `bhc_processed.db` — Workflow State
| Table | What it stores |
|---|---|
| `processed_clients` | Status, payment, quote ref, timestamps per client |
| `quote_sequences` | Daily sequence counters for reference numbers |

**Schema versioning:** `CONFIG_SCHEMA_VERSION = "7"`. When this version changes, the app recreates the database automatically.
> If you delete `data/bhc_config.db`, it is recreated with all default values on next startup.

**Passwords** are stored as PBKDF2-SHA256 with 200,000 iterations — never in plain text.

---

### 3.8 API Reference

All endpoints are under the prefix `/api/bhc/`. Full interactive docs: http://127.0.0.1:7860/docs

#### Authentication
| Method | Path | Description |
|---|---|---|
| POST | `/auth/login` | Login, returns session cookie |
| POST | `/auth/logout` | Invalidate session |
| POST | `/auth/register` | Self-registration (requires admin approval) |
| POST | `/auth/change-password` | Change own password |
| GET | `/auth/security-questions` | List available security questions |
| POST | `/auth/security-question/lookup` | Verify security Q&A for password reset |
| POST | `/auth/forgot-password` | Reset password after security question |

#### Clients & Workflow
| Method | Path | Description |
|---|---|---|
| GET | `/clients` | All clients with filters (search, status, payment, date) |
| GET | `/clients/pending` | Only unprocessed (Pending) clients |
| GET | `/clients/all` | All clients including processed |
| GET | `/client/{name}` | Single client by name |
| POST | `/generate-quote` | Generate PDF, assign reference number |
| POST | `/update-status` | Change status and/or payment |
| GET | `/dashboard` | Summary counts and revenue totals |
| GET | `/excel-status` | Check if Excel source is reachable |
| POST | `/upload-excel` | Upload a local Excel file as data source |

#### Downloads & Exports
| Method | Path | Description |
|---|---|---|
| POST | `/download/pdf` | Download generated PDF |
| POST | `/preview/pdf` | Inline PDF preview |
| POST | `/email-draft` | Generate .eml email draft |
| GET | `/export` | Export filtered clients to Excel |

#### Admin — Config
| Method | Path | Description |
|---|---|---|
| GET | `/admin/config` | All admin configuration |
| PUT | `/admin/company` | Update company settings |
| PUT | `/admin/document` | Update document/content settings |
| PUT | `/admin/pricing` | Update pricing slabs |
| GET | `/admin/scope-of-work` | Get scope templates |
| PUT | `/admin/scope-of-work` | Update scope templates |
| PUT | `/admin/support-documents` | Update support document lists |

#### Admin — Quotation Sections
| Method | Path | Description |
|---|---|---|
| GET | `/admin/quotation-sections` | List all sections in order |
| POST | `/admin/quotation-sections` | Create a new custom section |
| PUT | `/admin/quotation-sections/reorder` | Save new sort order |
| PUT | `/admin/quotation-sections/{id}` | Update heading/content/visibility |
| DELETE | `/admin/quotation-sections/{id}` | Delete custom section (system sections protected) |

#### Admin — Users
| Method | Path | Description |
|---|---|---|
| GET | `/admin/users` | List all users |
| POST | `/admin/users` | Create user (admin-created) |
| POST | `/admin/users/approve` | Approve a pending registration |
| POST | `/admin/users/reset-password` | Force reset user password |
| GET | `/admin/audit-events` | Audit log |

#### User Profile
| Method | Path | Description |
|---|---|---|
| PUT | `/user/profile` | Update name and designation |
| POST | `/user/signature` | Upload signature image |
| GET | `/user/signature/{email}` | Get signature image |
| GET | `/pricing-config` | Public pricing config (for quote form) |

---

### 3.9 Running Tests

The test suite has **19 tests** across 5 files. All use isolated temporary SQLite databases — no shared state.

```powershell
# Run all tests
.\.venv\Scripts\Activate.ps1
python -m pytest backend\tests -v

# Run a specific test file
python -m pytest backend\tests\test_pricing_engine.py -v

# Run tests with output visible (useful for debugging)
python -m pytest backend\tests -v -s
```

Expected output: `19 passed` in under 15 seconds.

**What each test file covers:**

| File | Tests |
|---|---|
| `test_config_db.py` | DB initialization, defaults, company/document/pricing CRUD |
| `test_dashboard_summary.py` | Revenue calculations, daily quote reference numbering |
| `test_pricing_engine.py` | Slab boundaries, override price, RCC/steel/both structure types |
| `test_user_auth.py` | Bootstrap admin, session creation, password change, security Q reset |
| `test_workflow_rules.py` | Valid and invalid status+payment combinations |

**Always run tests before pushing any change.** If a test fails after your edit, fix it before committing.

---

### 3.10 Common Development Tasks

#### Add a new environment variable
1. Add the key to `backend/.env.example` with a comment explaining it
2. Read it in `backend/app/config.py` using `get_env()`
3. Use the config constant wherever needed

#### Add a new API endpoint
1. Open `backend/app/routes/bhc_routes.py`
2. Add a Pydantic request model near the top of the file if the endpoint takes a body
3. Add the route function. Follow the existing pattern: call `ensure_authenticated(request)` or `ensure_admin(request)`, do the work, return a dict
4. Test it with the Swagger UI at http://127.0.0.1:7860/docs

#### Add a new admin config field
1. Add the default value to the relevant `DEFAULT_*` dict in `bhc_config_db.py`
2. Add read/write logic in the relevant `get_*` and `update_*` functions
3. Bump `CONFIG_SCHEMA_VERSION` by one (e.g. `"7"` → `"8"`)  
   > **Important:** Bumping the schema version will delete and recreate `bhc_config.db` on next startup. All custom data will be reset to defaults. In production, use migration logic instead of a version bump.
4. Add the field to the admin panel HTML in `frontend/bhc/index.html`
5. Bind the field in `populateAdminForm()` in `script.js`
6. Add a save handler or extend the relevant existing save function

#### Add a new quotation section (via code, not UI)
1. Open `bhc_config_db.py`
2. Add an entry to `DEFAULT_QUOTATION_SECTIONS` list
3. Add rendering logic in `bhc_output_generator.py` in the `generate_quote_pdf` function, inside the `for sec in visible_sections:` loop

#### Modify the PDF layout
- All PDF generation is in `backend/app/services/bhc_output_generator.py`
- The library used is `fpdf` (version 1.7.2 — legacy, latin-1 only)
- Use `_pdf_safe()` on every string before passing to `pdf.cell()` or `pdf.multi_cell()` — this prevents crashes on special characters
- Test by generating a quote through the UI after your change

#### Modify the frontend UI
- Edit `frontend/bhc/index.html`, `style.css`, or `script.js` directly
- Hard-refresh the browser (Ctrl+F5) to clear cache after each change
- The CSS uses CSS custom properties (variables) defined at the top of `style.css` — always use these instead of hardcoded colors
- All UI state is managed in a global `state` object in `script.js`

---

### 3.11 Debugging Tips

**Server won't start**
- Make sure the virtual environment is active: you should see `(.venv)` in the prompt
- Check for import errors in the terminal output
- Make sure `backend/requirements.txt` packages are all installed: `pip install -r backend\requirements.txt`

**"Module not found" errors**
- Always run from the project root directory, not from inside `backend/`
- The `uvicorn backend.app.main:app` command must be run from the folder that contains `backend/`

**Excel data not loading**
- Check the terminal — it will print the Excel path it's trying to open
- Set `EXCEL_FILE_PATH` in `.env` to the absolute path of your Excel file
- Or use the **Upload Excel** button in the app to upload a local file

**Database errors after pulling new code**
- If `CONFIG_SCHEMA_VERSION` has changed, delete `data/bhc_config.db` — it will be recreated
- Never delete `bhc_processed.db` unless you want to lose all status/payment history

**PDF generation fails**
- Check the terminal for the actual Python error
- The most common cause is a non-latin-1 character in a text field — add the character to the `replacements` dict in `_pdf_safe()` in `bhc_output_generator.py`

**Admin Panel shows blank**
- Open browser DevTools (F12) → Console tab — look for red errors
- Most common cause: a JS error in `populateAdminForm()` due to a missing field in the API response

**Test failures**
- Run `python -m pytest backend\tests -v -s` to see full output
- Tests use `tmp_path` (pytest fixture) for isolated DB files — they never touch your real `data/` folder

---

### 3.12 Contributing a Fix or Feature

1. **Create a branch** with a descriptive name:
   ```powershell
   git checkout -b fix/pdf-encoding-issue
   # or
   git checkout -b feature/email-notifications
   ```

2. **Make your changes.** Keep each commit focused on one thing.

3. **Run all tests and make sure they pass:**
   ```powershell
   python -m pytest backend\tests -v
   ```

4. **Add a test** if you added new logic. Place it in the relevant test file or create a new one in `backend/tests/`.

5. **Commit with a clear message:**
   ```powershell
   git add .
   git commit -m "fix: handle rupee symbol in PDF safe encoder"
   ```

6. **Push and open a pull request:**
   ```powershell
   git push bhc fix/pdf-encoding-issue
   ```
   Then open a Pull Request on GitHub targeting the `main` branch.

**Commit message format:**
- `feat:` — new feature
- `fix:` — bug fix
- `refactor:` — code improvement with no behavior change
- `test:` — adding or updating tests
- `docs:` — documentation only
- `chore:` — dependency updates, config changes

---

## 4. Security Notes

- **Password hashing:** PBKDF2-SHA256, 200,000 iterations. Never stored in plain text.
- **Session cookies:** HTTP-only cookies, 8-hour TTL, invalidated on logout.
- **Domain restriction:** Only `@ind.tuv.com` email addresses can register or log in.
- **Admin actions are audit-logged:** Every configuration change, user creation, and section modification is recorded with the actor's email, timestamp, and severity.
- **Input validation:** All admin endpoints use Pydantic request models for type and format validation.
- **SQL injection prevention:** All database queries use parameterized statements — no string concatenation in SQL.
- **System sections are protected:** The 14 default quotation sections cannot be deleted via the API — only custom sections can be deleted.
- **Do not commit `.env`** — it is listed in `.gitignore`. Never put real credentials in `backend/.env.example`.

---

## 5. Known Limitations

- The PDF library (`fpdf 1.7.2`) only supports **latin-1 encoding**. Characters like ₹ (Indian Rupee) are replaced with `Rs.` automatically. If you see garbled characters in the PDF, add the problematic character to the `_pdf_safe()` function in `bhc_output_generator.py`.
- The app is designed for **Windows** (the Excel file path logic, activation script, and OneDrive path detection are Windows-specific).
- There is **no email sending** built in — the "email draft" feature creates a `.eml` file that you open and send manually in Outlook.
- Session state is **not distributed** — if you run two server instances, sessions from one will not work on the other.
- The Excel source is **read-only** — the app never writes back to the Excel file. All processed state (status, payment, quotes) is stored in SQLite.

---

## 6. Changelog

### v I.05 (April 2026) — Quotation Sections Management
- **New:** Quotation Sections Manager in Admin Panel — full plug-and-play control over PDF sections
- **New:** 14 default system sections with show/hide toggle, drag-to-reorder, inline edit
- **New:** Add custom sections with interactive builder (Numbered List, Paragraphs, Table)
- **New:** Insert position selector when adding custom sections
- **New:** PDF generator now reads all sections from database — zero hardcoded content
- **New:** Audit logging for all section create/edit/delete/reorder events
- **Fix:** Route ordering bug for `/admin/quotation-sections/reorder` endpoint

### v I.04 and earlier
- Scope of work templates per structure type
- Support document templates
- User self-registration with admin approval
- Security question-based password recovery
- Daily quote reference number sequencing
- PDF preview in-browser
- Email draft (.eml) generation
- Excel export with filters
- Audit log

