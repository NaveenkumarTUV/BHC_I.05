# BHC Quotation Generator — v I.06

**TÜV Rheinland (India) Pvt. Ltd.**  
Building Health Check-Up (BHC) & Detailed Examination Quotation (DEQ) — Quotation Management System

An internal web application that manages the full lifecycle of BHC and DEQ enquiries: pulling raw Microsoft Forms data, generating professional PDF quotations, tracking workflow status, managing payments, exporting reports — all through a single browser tab with zero external cloud dependency.

---

## Table of Contents

1. [What This Tool Does](#1-what-this-tool-does)
2. [User Guide — Full Feature Walkthrough](#2-user-guide--full-feature-walkthrough)
   - [Logging In](#21-logging-in)
   - [Dashboard](#22-dashboard)
   - [New Enquiries](#23-new-enquiries)
   - [BHC Quotation Studio](#24-bhc-quotation-studio)
   - [BHC Pipeline](#25-bhc-pipeline)
   - [Updating Status and Payments](#26-updating-status-and-payments)
   - [DEQ Module (Detailed Examination Quotation)](#27-deq-module-detailed-examination-quotation)
   - [Exporting Data](#28-exporting-data)
   - [Admin Panel](#29-admin-panel)
3. [Developer Guide — Setup to Contribution](#3-developer-guide--setup-to-contribution)
   - [Prerequisites](#31-prerequisites)
   - [First-Time Setup](#32-first-time-setup)
   - [Configure Environment](#33-configure-environment)
   - [Run the Application](#34-run-the-application)
   - [Project Structure Explained](#35-project-structure-explained)
   - [How Data Flows Through the App](#36-how-data-flows-through-the-app)
   - [Database Design](#37-database-design)
   - [API Reference](#38-api-reference)
   - [Common Development Tasks](#39-common-development-tasks)
   - [Enabling / Disabling the DEQ Module](#310-enabling--disabling-the-deq-module)
   - [Debugging Tips](#311-debugging-tips)
   - [Contributing a Fix or Feature](#312-contributing-a-fix-or-feature)
4. [Security Notes](#4-security-notes)
5. [Known Limitations](#5-known-limitations)
6. [Changelog](#6-changelog)

---

## 1. What This Tool Does

The BHC Quotation Generator is an internal tool built for the TÜV Rheinland India civil engineering team. It supports two modules:

### BHC — Building Health Check-Up

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

### DEQ — Detailed Examination Quotation

```
BHC assessment identifies specific issues
        ↓
DEQ quotation raised, linked to originating BHC record
        ↓
Independent pipeline, pricing, and PDF generation
        ↓
Status / payment tracking → Export
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

After login you land on the **Home** (Dashboard) tab. It shows real-time summary cards:

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

### 2.3 New Enquiries

The **New Enquiries** tab displays all unprocessed clients from the Excel source. Use the search box and filters:

- **Search** — by client name, phone, city, or property name
- **Property type filter** — Residential / Commercial / Industrial / etc.

Click on a client row to expand details and proceed with quotation generation.

---

### 2.4 BHC Quotation Studio

The **Quote Studio** tab is where you generate, preview, and download BHC quotation PDFs:

1. Select a client from the **New Enquiries** tab (Pending status).
2. Review the auto-calculated price (based on area slabs configured in Admin).
3. Optionally **override the final price** manually.
4. Select **Structure Type**: RCC, Steel, or Both.
5. Click **Generate Quote**.

The system will:
- Assign a unique daily reference number (e.g. `BEN-HC-TUVR-20260417-0001`)
- Build the PDF using all visible sections configured in the Quotation Sections Manager
- Allow you to **Preview** the PDF in-browser before downloading
- Offer a **Download PDF** button (with your uploaded signature embedded)
- Offer an **Email Draft** button (creates a `.eml` file for Outlook)

**Quote reference numbers** reset their daily counter each new day and are stored permanently so they never repeat.

---

### 2.5 BHC Pipeline

The **BHC Pipeline** tab shows all processed clients (Quoted, Converted, Dropped). Each row supports:

- Inline **status** change via dropdown
- Inline **payment** status change via dropdown
- Inline **remarks** text field
- Auto-save to database (sync pill shows Saved / Saving / Error)
- **Download PDF** and **Delete** actions

Use the search box and status/payment filters to find specific records. Click **Export to Excel** to download filtered data.

---

### 2.6 Updating Status and Payments

**Status transitions allowed:**

| From | To | Allowed? |
|---|---|---|
| Pending | Quoted | ✅ (automatic on quote generation) |
| Quoted | Converted | ✅ |
| Quoted | Dropped | ✅ |
| Converted | Dropped | ✅ |
| Any | Pending | ❌ (cannot go back) |

**Payment status:**

| Status | Payment options |
|---|---|
| Quoted | Pending only |
| Converted | Pending or Paid |
| Dropped | Pending only |

---

### 2.7 DEQ Module (Detailed Examination Quotation)

> **Note:** The DEQ module ships in a **Coming Soon** state by default. To activate it, see [Section 3.11 — Enabling / Disabling the DEQ Module](#311-enabling--disabling-the-deq-module).

#### What is DEQ?

When a BHC assessment identifies specific issues — structural cracks, electrical faults, water seepage, facade damage — a **Detailed Examination Quotation** is raised. It links back to the originating BHC record and manages a separate, deeper investigation scope.

#### How it works

1. **A BHC assessment identifies issues** — cracks, structural defects, electrical faults, or water seepage.
2. **A DEQ quotation is raised**, linked to the BHC record, for a deeper examination of the identified issues.
3. **The DEQ module tracks its own pipeline**, statuses, payments, and generates a branded quotation PDF.

#### DEQ Tab Features (when enabled)

| Feature | Description |
|---|---|
| **DEQ Dashboard** | Total DEQs, Converted count, Total Quoted revenue, Paid Revenue — four metric cards |
| **New DEQ Form** | Select a linked BHC record (optional), enter client details, examination type, issue description, and quoted amount |
| **DEQ Pipeline** | Table of all DEQ records with inline status/payment/remarks editing and auto-save |
| **Examination Types** | Structural, Electrical, Plumbing, Fire Safety, Facade, Comprehensive, Other |
| **DEQ PDF Generation** | Download branded quotation PDF per record, with configurable sections |
| **DEQ Export** | Export all DEQ records to Excel |
| **DEQ Quotation Studio** | Admin-only section manager — same premium UI as BHC (drag-to-reorder, show/hide toggle, content builder) |

**DEQ Reference Number Format:** `BEN-DE-TUVR-YYYYMMDD-NNNN`

---

### 2.8 Exporting Data

**BHC Export** — Use the **Export to Excel** button on the BHC Pipeline tab. Filters applied in the view carry over to the export.

**DEQ Export** — Use the **Export to Excel** button on the DEQ tab.

**Email Draft** — Available per client on the BHC quotation generation screen. Downloads a `.eml` file with the client's email pre-filled, ready to open and send in Outlook.

---

### 2.9 Admin Panel

The Admin Panel is only visible to **admin accounts**. Access it from the tab navigation bar.

#### Company Settings
Set the company name, address, contact details, GST percentage, and **urgency surcharge percentage**. These values appear on every generated quotation PDF.

> **Note:** Setting urgency surcharge to **0%** is allowed — the surcharge line is automatically hidden from the PDF when the value is zero.

#### Document Settings
Control what appears in the standard sections of the PDF:
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

#### BHC Quotation Sections Manager
Controls **every section** of the generated BHC PDF quotation:

- **Show / Hide** any section using the toggle switch — hidden sections are skipped in PDF generation
- **Reorder** sections by dragging the ≡ handle up or down — PDF order follows this order exactly
- **Edit** section heading and content directly (click **Edit** button)
- **Add a custom section** using **+ Add New Section**:
  1. Enter a **Section Heading** (e.g. "Special Safety Conditions")
  2. Choose **Content Type**: Numbered List, Paragraphs, or Table
  3. Add content items using the interactive builder
  4. Click **Add Section**
- **Delete** any custom (non-system) section

System sections (marked with **System** badge) cannot be deleted but can be hidden and reordered.

#### DEQ Quotation Sections Manager
Same premium interface as BHC, but manages the sections used in DEQ quotation PDFs. Includes 8 default sections. Available when the DEQ module is enabled.

#### User Management
- View all registered users and their approval status
- **Approve** pending registration requests
- **Deactivate** or **reactivate** existing user accounts
- **Toggle admin access** for any user (cannot change your own role)
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
git clone https://github.com/NaveenkumarTUV/BHC_I.06.git
cd BHC_I.06
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

Create a `.env` file in the project root. See [Section 3.3](#33-configure-environment) for the required variables.

---

### 3.3 Configure Environment

Open `.env` in any text editor (Notepad, VS Code, etc.) and set the values:

```ini
# Path to the Microsoft Forms Excel source file
# Leave blank to use data/bhc_enquiries.xlsx as fallback
EXCEL_FILE_PATH=C:\path\to\your\enquiries.xlsx

# Leave all DB paths blank to auto-create SQLite files in data/
BHC_PROCESSED_DB_PATH=
BHC_CONFIG_DB_PATH=

# Data directory override (default: data/)
DATA_DIR_PATH=

# Exports directory override (network drive recommended)
# Exports are organised as: <path>/bhc/YYYY/MM/ and <path>/deq/YYYY/MM/
# Leave blank to use data/exports/ as fallback
EXPORTS_BASE_PATH=I:\Bangalore\INDUSTRY\MTL-AI-Projects\Civil\exports

# Server settings
SERVER_HOST=127.0.0.1
SERVER_PORT=7860
DEBUG_MODE=true

# CORS allowed origins (comma-separated, or * for all)
ALLOWED_ORIGINS=*
```

**Environment variable reference:**

| Variable | Default | Purpose |
|---|---|---|
| `EXCEL_FILE_PATH` | *(empty)* | Absolute path to the Microsoft Forms Excel workbook |
| `BHC_PROCESSED_DB_PATH` | `data/bhc_processed.db` | Override path for the workflow SQLite database |
| `BHC_CONFIG_DB_PATH` | `data/bhc_config.db` | Override path for the config SQLite database |
| `DATA_DIR_PATH` | `data/` | Override for the data directory root |
| `EXPORTS_BASE_PATH` | `data/exports/` | Override for exports root (network drive). Auto-creates `bhc/YYYY/MM/` and `deq/YYYY/MM/` sub-folders |
| `SERVER_HOST` | `127.0.0.1` | Bind address for uvicorn |
| `SERVER_PORT` | `7860` | Port for uvicorn |
| `DEBUG_MODE` | `false` | Enable verbose logging |
| `ALLOWED_ORIGINS` | `*` | CORS allowed origins (comma-separated) |

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
- **API docs** → http://127.0.0.1:7860/docs *(auto-generated Swagger UI, useful for testing endpoints)*
- **Health check** → http://127.0.0.1:7860/api/health
- **Session info** → http://127.0.0.1:7860/api/session

The `--reload` flag means the server restarts automatically every time you save a Python file — useful during development.

*
---

### 3.5 Project Structure Explained

```
Quotation_Generator/
│
├── .env                            ← Your local environment config (never commit this)
├── README.md                       ← This file
│
├── backend/
│   ├── __init__.py
│   ├── requirements.txt            ← Python package list (11 packages)
│   └── app/
│       ├── __init__.py
│       ├── main.py                 ← FastAPI app factory, startup, middleware, static mount
│       ├── config.py               ← Reads all environment variables from .env
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── bhc_routes.py       ← BHC API endpoints (~41 routes, prefix /api/bhc)
│       │   └── deq_routes.py       ← DEQ API endpoints (12 routes, prefix /api/deq)
│       ├── services/
│       │   ├── __init__.py
│       │   ├── bhc_admin_auth.py       ← Session/cookie auth helpers
│       │   ├── bhc_config_db.py        ← Config SQLite: users, pricing, settings, BHC + DEQ sections
│       │   ├── bhc_workflow_db.py      ← Workflow SQLite: processed BHC clients, quote sequences
│       │   ├── bhc_workflow_service.py ← Excel → DB bridge, client merging, caching (120s TTL)
│       │   ├── bhc_pricing_engine.py   ← Area-slab price calculation
│       │   ├── bhc_output_generator.py ← BHC PDF generation (fpdf)
│       │   ├── bhc_excel_reader.py     ← Raw Excel parsing (openpyxl/pandas)
│       │   ├── deq_db.py              ← DEQ SQLite CRUD (records in bhc_processed.db)
│       │   └── deq_output_generator.py ← DEQ PDF generation (fpdf)
│       └── utils/
│           ├── __init__.py
│           └── paths.py                ← DATA_DIR, EXPORTS_DIR, FRONTEND_DIR constants
│
├── frontend/
│   └── bhc/
│       ├── index.html              ← Single-page application shell (6 tabs)
│       ├── script.js               ← All UI logic (~4000 lines, vanilla JS)
│       └── style.css               ← All styling (~2000 lines, CSS custom properties)
│
├── data/
│   ├── assets/                    ← Static assets (tuv_logo.png for PDFs)
│   └── exports/
│       ├── bhc/YYYY/MM/            ← Generated BHC PDFs, email drafts, Excel exports (year/month folders)
│       └── deq/YYYY/MM/            ← Generated DEQ PDFs and Excel exports (year/month folders)
```

**Key rule:** The frontend (`index.html` / `script.js` / `style.css`) is **pure vanilla JS** — no build tools, no npm, no webpack. You edit the file and refresh the browser. That's it.

---

### 3.6 How Data Flows Through the App

**On page load:**
1. Browser loads `index.html` → `script.js` calls `GET /api/session`
2. If authenticated → calls `GET /api/bhc/clients/pending` (Excel clients), `GET /api/bhc/clients/all` (DB clients), `GET /api/bhc/dashboard`
3. Admin users additionally load `GET /api/bhc/admin/config`

**On BHC Generate Quote:**
1. `POST /api/bhc/generate-quote` with client data and optional price override
2. Backend: `bhc_pricing_engine.py` calculates price → `bhc_output_generator.py` calls `list_quotation_sections()` from DB → builds PDF using fpdf → saves to `data/exports/bhc/`
3. Frontend receives file path → shows preview/download buttons

**On DEQ Create:**
1. `POST /api/deq/pipeline` with client details, examination type, amount, and optional BHC link
2. Backend: `deq_db.py` creates record in `bhc_processed.db` → assigns reference number (`BEN-DE-TUVR-...`)
3. Frontend refreshes the DEQ pipeline table

**On DEQ PDF Download:**
1. `POST /api/deq/download/pdf/{deq_id}`
2. Backend: `deq_output_generator.py` reads DEQ sections from `bhc_config_db.py` → builds PDF → returns file

**On Admin Config Save:**
1. Any `PUT /api/bhc/admin/company` (or similar) endpoint
2. Backend validates via Pydantic model, writes to SQLite (`bhc_config.db`)
3. Frontend refreshes admin config from `GET /api/bhc/admin/config`

**Quotation Sections Flow (BHC & DEQ):**
1. `GET /api/bhc/admin/quotation-sections` or `GET /api/deq/admin/sections` → returns sections in display order
2. Toggle/edit/reorder/add/delete via dedicated PUT/POST/DELETE endpoints
3. On next PDF generation, the output generator reads sections fresh from DB — all changes are reflected immediately

---

### 3.7 Database Design

The app uses **two SQLite databases** (auto-created on first run):

#### `bhc_config.db` — Configuration, Auth & Sections
| Table | What it stores |
|---|---|
| `config_meta` | Schema version, key-value config pairs |
| `pricing_slabs` | Area-based pricing (standard + new building categories) |
| `company_settings` | Company name, address, contact, GST%, urgency surcharge% |
| `document_settings` | About Us, deliverables, payment terms, etc. |
| `scope_of_work` | Per-structure-type scope templates |
| `users` | User accounts, PBKDF2-SHA256 password hashes, approval status |
| `sessions` | Active login sessions (8-hour TTL) |
| `audit_events` | Security + workflow audit trail |
| `quotation_sections` | BHC PDF sections: 14 system defaults + custom |
| `deq_sections` | DEQ PDF sections: 8 system defaults + custom |

#### `bhc_processed.db` — Workflow State (BHC + DEQ)
| Table | What it stores |
|---|---|
| `processed_clients` | BHC status, payment, quote ref, timestamps per client |
| `quote_sequences` | Daily sequence counters for BHC reference numbers |
| `deq_records` | DEQ pipeline records: BHC link, exam type, amount, status, payment |

**Schema versioning:** `CONFIG_SCHEMA_VERSION = "7"`. When this version changes, the app recreates `bhc_config.db` automatically.
> If you delete `data/bhc_config.db`, it is recreated with all default values on next startup. `bhc_processed.db` holds client/DEQ data — do not delete unless you want to lose all history.

**Passwords** are stored as PBKDF2-SHA256 with 200,000 iterations — never in plain text.

---

### 3.8 API Reference

Full interactive docs are available at: http://127.0.0.1:7860/docs

#### App-Level Routes
| Method | Path | Description |
|---|---|---|
| GET | `/` | Redirect to `/bhc` |
| GET | `/api/health` | Health check endpoint |
| GET | `/api/session` | Current user session info |
| GET | `/api/assets/tuv-logo` | TÜV logo PNG image |

#### BHC Authentication (`/api/bhc/auth/`)
| Method | Path | Description |
|---|---|---|
| POST | `/auth/login` | Login, returns session cookie |
| POST | `/auth/logout` | Invalidate session |
| POST | `/auth/register` | Self-registration (requires admin approval) |
| POST | `/auth/change-password` | Change own password |
| GET | `/auth/security-questions` | List available security questions |
| POST | `/auth/security-question/lookup` | Get security question for an email |
| POST | `/auth/forgot-password` | Reset password after security Q&A |

#### BHC Clients & Workflow (`/api/bhc/`)
| Method | Path | Description |
|---|---|---|
| GET | `/clients` | Backward-compatible alias (pending clients) |
| GET | `/clients/pending` | Unprocessed clients from Excel |
| GET | `/clients/all` | All processed clients from DB |
| GET | `/client/{name}` | Single client by name |
| POST | `/generate-quote` | Generate BHC PDF, assign reference number |
| POST | `/update-status` | Change status and/or payment |
| GET | `/dashboard` | Summary counts and revenue totals |
| GET | `/excel-status` | Check if Excel source is reachable |
| POST | `/upload-excel` | Upload a local Excel file as data source |
| GET | `/pricing-config` | Current pricing slabs |

#### BHC Downloads & Exports (`/api/bhc/`)
| Method | Path | Description |
|---|---|---|
| POST | `/download/pdf` | Download generated PDF (with signature) |
| POST | `/preview/pdf` | Inline PDF preview (no signature) |
| POST | `/email-draft` | Generate `.eml` email draft with attachment |
| GET | `/export` | Export filtered clients to Excel |

#### BHC Admin — Configuration (`/api/bhc/admin/`)
| Method | Path | Description |
|---|---|---|
| GET | `/admin/config` | Full admin configuration |
| PUT | `/admin/company` | Update company settings |
| PUT | `/admin/document` | Update document/content settings |
| PUT | `/admin/pricing` | Replace pricing slabs |
| GET | `/admin/scope-of-work` | Get scope + support document templates |
| PUT | `/admin/scope-of-work` | Update scope templates |
| PUT | `/admin/support-documents` | Update support document lists |

#### BHC Admin — Quotation Sections (`/api/bhc/admin/`)
| Method | Path | Description |
|---|---|---|
| GET | `/admin/quotation-sections` | List all BHC sections in order |
| POST | `/admin/quotation-sections` | Create a new custom section |
| PUT | `/admin/quotation-sections/reorder` | Save new sort order |
| PUT | `/admin/quotation-sections/{id}` | Update heading/content/visibility |
| DELETE | `/admin/quotation-sections/{id}` | Delete custom section |

#### BHC Admin — Users (`/api/bhc/admin/`)
| Method | Path | Description |
|---|---|---|
| GET | `/admin/users` | List all users |
| POST | `/admin/users/approve` | Approve a pending registration |
| POST | `/admin/users/toggle-active` | Activate or deactivate a user |
| POST | `/admin/users/toggle-admin` | Grant or revoke admin access |
| POST | `/admin/users/reset-password` | Force reset user password |
| GET | `/admin/audit-events` | Audit log |

#### BHC User Profile (`/api/bhc/user/`)
| Method | Path | Description |
|---|---|---|
| PUT | `/user/profile` | Update name, designation, security question |
| POST | `/user/signature` | Upload signature image (PNG/JPEG, max 500 KB) |
| GET | `/user/signature/{email}` | Retrieve signature image |

#### DEQ Pipeline (`/api/deq/`)
| Method | Path | Description |
|---|---|---|
| GET | `/pipeline` | List all DEQ records |
| POST | `/pipeline` | Create a new DEQ record |
| PUT | `/pipeline/{deq_id}` | Update DEQ status/payment/remarks |
| DELETE | `/pipeline/{deq_id}` | Delete DEQ record |
| GET | `/dashboard` | DEQ summary counts and revenue |
| GET | `/bhc-clients` | List BHC pipeline records for linking |

#### DEQ Downloads & Exports (`/api/deq/`)
| Method | Path | Description |
|---|---|---|
| POST | `/download/pdf/{deq_id}` | Generate and download DEQ PDF |
| GET | `/export` | Export all DEQ records to Excel |

#### DEQ Admin — Sections (`/api/deq/admin/`)
| Method | Path | Description |
|---|---|---|
| GET | `/admin/sections` | List all DEQ sections |
| POST | `/admin/sections` | Create DEQ section |
| PUT | `/admin/sections/reorder` | Reorder DEQ sections |
| PUT | `/admin/sections/{section_id}` | Update DEQ section |
| DELETE | `/admin/sections/{section_id}` | Delete DEQ section |

---

### 3.9 Common Development Tasks

#### Add a new environment variable
1. Add the key to your `.env` file
2. Read it in `backend/app/config.py` using `get_env()`
3. Use the config constant wherever needed

#### Add a new BHC API endpoint
1. Open `backend/app/routes/bhc_routes.py`
2. Add a Pydantic request model near the top if the endpoint takes a body
3. Add the route function — follow the existing pattern: call `ensure_authenticated(request)` or `ensure_admin(request)`, do the work, return a dict
4. Test it with the Swagger UI at http://127.0.0.1:7860/docs

#### Add a new DEQ API endpoint
1. Open `backend/app/routes/deq_routes.py`
2. Follow the same pattern as BHC routes — Pydantic model + route function
3. The DEQ router uses prefix `/api/deq`

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
2. Add an entry to `DEFAULT_QUOTATION_SECTIONS` (for BHC) or `DEFAULT_DEQ_SECTIONS` (for DEQ)
3. Add rendering logic in the corresponding output generator's `for sec in visible_sections:` loop

#### Modify the PDF layout
- BHC PDFs → `backend/app/services/bhc_output_generator.py`
- DEQ PDFs → `backend/app/services/deq_output_generator.py`
- The library is `fpdf` (version 1.7.2 — legacy, latin-1 only)
- Use `_pdf_safe()` on every string before passing to `pdf.cell()` or `pdf.multi_cell()`
- Test by generating a quote through the UI after your change

#### Modify the frontend UI
- Edit `frontend/bhc/index.html`, `style.css`, or `script.js` directly
- Hard-refresh the browser (Ctrl+F5) to clear cache after each change
- Bump the cache version in the `<link>` and `<script>` tags in `index.html` (e.g. `?v=20260420k` → `?v=20260420m`)
- The CSS uses CSS custom properties (variables) defined at the top of `style.css` — always use these instead of hardcoded colors
- All UI state is managed in a global `state` object in `script.js`

---

### 3.10 Enabling / Disabling the DEQ Module

The DEQ module is controlled by a single JavaScript flag at the top of the DEQ module section in `frontend/bhc/script.js`:

```javascript
const DEQ_ENABLED = false; // Set to true to activate the DEQ module
```

**To activate DEQ**, change `false` → `true`:

```javascript
const DEQ_ENABLED = true;
```

**To deactivate DEQ**, change `true` → `false`:

```javascript
const DEQ_ENABLED = false;
```

When **disabled** (`false`):
- Clicking the DEQ tab shows a premium "Coming Soon" screen explaining what DEQ is
- No API calls are made to DEQ endpoints
- The DEQ pipeline, form, studio, and stats are all hidden

When **enabled** (`true`):
- The Coming Soon screen is hidden
- Full DEQ functionality is available: dashboard stats, new DEQ form, pipeline table, PDF generation, export, and the Quotation Sections manager (admin)

> The backend DEQ routes are always active regardless of this flag. The flag only controls the frontend visibility.

---

### 3.11 Debugging Tips

**Server won't start**
- Make sure the virtual environment is active: you should see `(.venv)` in the prompt
- Check for import errors in the terminal output
- Make sure all packages are installed: `pip install -r backend\requirements.txt`

**"Module not found" errors**
- Always run from the project root directory, not from inside `backend/`
- The `uvicorn backend.app.main:app` command must be run from the folder that contains `backend/`

**Excel data not loading**
- Check the terminal — it prints the Excel path it's trying to open
- Set `EXCEL_FILE_PATH` in `.env` to the absolute path of your Excel file
- Or use the **Upload Excel** button in the app to upload a local file

**Database errors after pulling new code**
- If `CONFIG_SCHEMA_VERSION` has changed, delete `data/bhc_config.db` — it will be recreated
- Never delete `bhc_processed.db` unless you want to lose all BHC and DEQ history

**PDF generation fails**
- Check the terminal for the actual Python error
- The most common cause is a non-latin-1 character — add the character to the `replacements` dict in `_pdf_safe()` in the relevant output generator

**Admin Panel shows blank**
- Open browser DevTools (F12) → Console tab — look for red errors
- Most common cause: a JS error in `populateAdminForm()` due to a missing field in the API response

**DEQ tab shows "Coming Soon" when it should be active**
- Check that `DEQ_ENABLED = true` in `script.js` (see [Section 3.10](#310-enabling--disabling-the-deq-module))
- Hard-refresh the browser (Ctrl+F5) to ensure the latest JS is loaded

---

### 3.12 Contributing a Fix or Feature

1. **Create a branch** with a descriptive name:
   ```powershell
   git checkout -b fix/pdf-encoding-issue
   # or
   git checkout -b feature/deq-email-draft
   ```

2. **Make your changes.** Keep each commit focused on one thing.

3. **Test your changes** manually through the UI and Swagger docs at http://127.0.0.1:7860/docs

4. **Commit with a clear message:**
   ```powershell
   git add .
   git commit -m "fix: handle rupee symbol in PDF safe encoder"
   ```

5. **Push and open a pull request:**
   ```powershell
   git push origin fix/pdf-encoding-issue
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
- **Input validation:** All endpoints use Pydantic request models for type and format validation.
- **SQL injection prevention:** All database queries use parameterized statements — no string concatenation in SQL.
- **System sections are protected:** Default quotation sections (BHC and DEQ) cannot be deleted via the API — only custom sections can be deleted.
- **Request IDs:** Every API response includes an `X-Request-ID` header (UUID) for tracing.
- **Do not commit `.env`** — it is listed in `.gitignore`. Never put real credentials in committed files.

---

## 5. Known Limitations

- The PDF library (`fpdf 1.7.2`) only supports **latin-1 encoding**. Characters like ₹ (Indian Rupee) are replaced with `Rs.` automatically. If you see garbled characters in the PDF, add the problematic character to the `_pdf_safe()` function in the relevant output generator.
- The app is designed for **Windows** (Excel file path logic, PowerShell activation script, and OneDrive path detection are Windows-specific).
- There is **no email sending** built in — the "email draft" feature creates a `.eml` file that you open and send manually in Outlook.
- Session state is **not distributed** — if you run two server instances, sessions from one will not work on the other.
- The Excel source is **read-only** — the app never writes back to the Excel file. All processed state (status, payment, quotes) is stored in SQLite.
- The DEQ module ships **disabled by default** (Coming Soon screen). Enable it by setting `DEQ_ENABLED = true` in `script.js`.

---

## 6. Changelog

### v I.06 (April 2026) — DEQ Module & UI Overhaul
- **New:** DEQ (Detailed Examination Quotation) module — full pipeline, dashboard, PDF generation, and Excel export
- **New:** DEQ records link to originating BHC assessments with examination type tracking
- **New:** DEQ Quotation Studio — 8 default sections, custom section builder, drag-to-reorder, show/hide toggle
- **New:** DEQ reference number format: `BEN-DE-TUVR-YYYYMMDD-NNNN`
- **New:** DEQ "Coming Soon" premium screen with `DEQ_ENABLED` toggle in `script.js`
- **New:** Premium modal design for both BHC and DEQ section builders (type cards, numbered builder items)
- **Fix:** Urgency surcharge now allows 0% — the surcharge line is suppressed in the PDF when set to zero
- **Fix:** Various sync-pill, confirmation modal, and API response handling fixes

### v I.05 (April 2026) — Quotation Sections Management
- **New:** Quotation Sections Manager in Admin Panel — full plug-and-play control over BHC PDF sections
- **New:** 14 default system sections with show/hide toggle, drag-to-reorder, inline edit
- **New:** Add custom sections with interactive builder (Numbered List, Paragraphs, Table)
- **New:** PDF generator reads all sections from database — zero hardcoded content
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

