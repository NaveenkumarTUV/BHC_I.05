# BHC Quotation Generator — v I.05

**TÜV Rheinland (India) Pvt. Ltd.** — Building Health Check-Up Quotation Management System

FastAPI-based internal tool for BHC enquiry processing, quotation generation, and lifecycle tracking.

## Features

- **Enquiry Dashboard** — Real-time pipeline from Microsoft Forms Excel
- **Automated Quotation** — Area-slab pricing, PDF generation with TÜV letterhead
- **Workflow Management** — Status tracking (Pending → Quoted → Converted/Dropped), payment lifecycle
- **Self-Registration** — New users register via login page; admin approves access
- **Security** — PBKDF2-SHA256 password hashing, session-cookie auth, security questions for password recovery
- **Admin Panel** — User management, pricing slabs, company settings, quotation content, scope-of-work templates
- **Export** — PDF download, email draft (.eml), Excel export with filters

## 1.  Onboarding in 10 Minutes

If you are new to this project, do these steps first.

1. Read [backend/app/main.py](backend/app/main.py).
2. Read [backend/app/routes/bhc_routes.py](backend/app/routes/bhc_routes.py).
3. Read [backend/app/services/bhc_workflow_service.py](backend/app/services/bhc_workflow_service.py).
4. Run the app locally and open the UI.
5. Run tests and confirm all pass.

After this, you will understand the complete request flow.

## 2. Prerequisites

- Windows 10 or 11
- Python 3.11+ (3.12 recommended)
- PowerShell
- Access to an enquiry Excel workbook (or use local fallback file)

## 3. Setup (Windows)

Run from project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

Create root environment file:

```powershell
Copy-Item backend\.env.example .env
```

## 4. Configure Environment Variables

Use [backend/.env.example](backend/.env.example) as reference.

Important keys:
- EXCEL_FILE_PATH: absolute path to source workbook (optional)
- BHC_PROCESSED_DB_PATH: processed workflow SQLite file (optional)
- BHC_CONFIG_DB_PATH: shared config/auth SQLite file (optional)
- BHC_ADMIN_PASSWORD: admin bootstrap and recovery password
- DATA_DIR_PATH: optional custom data folder
- SERVER_HOST: default host binding
- SERVER_PORT: default port
- DEBUG_MODE: development reload mode

Excel source priority used by app:
1. EXCEL_FILE_PATH from environment
2. known OneDrive form workbook names
3. data/bhc_enquiries.xlsx

## 5. Run the Application

From project root:

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --host 127.0.0.1 --port 7860 --reload
```

Open:
- http://127.0.0.1:7860/bhc

Session API check:
- http://127.0.0.1:7860/api/session

## 6. Login and Admin Notes

- Allowed login domain: @ind.tuv.com
- Seeded admin email: M.naveenkumar@ind.tuv.com
- If admin password is unknown, set BHC_ADMIN_PASSWORD in .env and restart app
- Passwords are stored as PBKDF2-SHA256 hashes in config SQLite

## 7. Run Tests

Run all backend tests:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest backend\tests -q
```

Run a single test file (example):

```powershell
python -m pytest backend\tests\test_pricing_engine.py -q
```

Expected result for healthy branch: all tests pass.

## 8. Project Structure and Responsibility

```text
Quotation_Generator/
├── backend/
│   ├── .env.example            # Environment template (copy to root .env)
│   ├── requirements.txt        # Pinned Python dependencies
│   ├── app/
│   │   ├── main.py             # FastAPI app bootstrap, middleware, health
│   │   ├── config.py           # Environment loading + validation
│   │   ├── routes/
│   │   │   └── bhc_routes.py   # All HTTP endpoints
│   │   ├── services/
│   │   │   ├── bhc_admin_auth.py       # Cookie auth helpers
│   │   │   ├── bhc_config_db.py        # Config/auth DB + user management
│   │   │   ├── bhc_workflow_db.py       # Processed enquiry DB operations
│   │   │   ├── bhc_workflow_service.py  # Business orchestration
│   │   │   ├── bhc_pricing_engine.py    # Area-slab pricing logic
│   │   │   ├── bhc_excel_reader.py      # Excel normalization
│   │   │   └── bhc_output_generator.py  # PDF generation (fpdf)
│   │   └── utils/
│   │       └── paths.py        # Cross-platform path helpers
│   └── tests/                  # pytest backend test suite
├── frontend/
│   └── bhc/                    # Single-page HTML/CSS/JS dashboard
│       ├── index.html
│       ├── style.css
│       └── script.js
├── data/                       # Runtime data (gitignored)
│   └── exports/bhc/            # Generated PDFs/Excel
├── .env                        # Local secrets (gitignored, never commit)
├── .gitignore
└── README.md
```

## 9. How a Request Flows (Mental Model)

1. Frontend calls an API route in [backend/app/routes/bhc_routes.py](backend/app/routes/bhc_routes.py).
2. Route validates input and auth, then calls service layer.
3. Service layer reads Excel, calculates pricing, and updates SQLite.
4. Route returns response or stream file download.

Keep route layer thin. Put reusable business logic in services.

## 10. Intern Development Rules

- Do not mix route code with heavy business logic.
- Prefer small, clear functions with explicit names.
- Add short comments only where logic is non-obvious.
- Keep API responses backward-compatible unless requested.
- Update tests when behavior changes.

## 11. Common Tasks

### Change pricing slabs
- Login as admin
- Use Admin Config UI to update slab ranges and quoted price
- Re-test with [backend/tests/test_pricing_engine.py](backend/tests/test_pricing_engine.py)

### Change company/profile text in quotation
- Use Admin Config UI document settings
- Verify PDF output from dashboard export

### Change Excel source
- Set EXCEL_FILE_PATH in .env, or
- use Select Excel File action in UI

## 12. Build Desktop EXE

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
.\backend\build_exe.ps1
```

Output:
- dist\BHC-Quotation-Generator.exe
- dist\.env
- dist\data\

## 13. Troubleshooting

### App starts but no enquiry records
- Confirm Excel path exists
- Check EXCEL_FILE_PATH in .env
- Confirm workbook is not locked by another process

### Login fails for valid user
- Confirm email domain is @ind.tuv.com
- Verify user exists in config DB
- For admin recovery, reset BHC_ADMIN_PASSWORD and restart app

### Tests failing unexpectedly
- Activate correct virtual environment
- Reinstall dependencies from requirements
- Run tests from project root

## 14. Useful Commands

```powershell
# start app
uvicorn backend.app.main:app --host 127.0.0.1 --port 7860 --reload

# run all backend tests
python -m pytest backend\tests -q

# run one test module
python -m pytest backend\tests\test_user_auth.py -q
```

## 15. Enterprise Readiness Features

The project now includes foundational enterprise behavior for supportability and production operations:

1. Startup configuration validation
- App validates critical env configuration at startup and fails fast on invalid values.

2. Health endpoint
- GET /api/health returns status, service name, version, and UTC timestamp.

3. Request correlation ID
- Every API response includes X-Request-ID.
- Error responses also include request_id in JSON for easier support ticket tracing.

4. Standardized error payload
- API errors return consistent fields: detail, error_code, request_id, timestamp.

5. Frontend API reliability
- Browser client enforces request timeout.
- GET requests retry once on transient failures.
- User-visible errors include request_id when available.

6. Enterprise operations UI
- New Operations tab provides:
- service health status and health timestamp
- config/workflow schema versions
- security audit events and workflow audit events (admin)

7. Schema maturity
- Config DB now tracks schema version in `schema_meta`.
- Workflow DB now tracks schema version in `schema_meta`.
- Processed workflow records now include `created_at`, `updated_at`, and row `version` for change tracking.
- Audit tables:
- `security_audit_events` in config DB
- `workflow_audit_events` in workflow DB

## 16. Support Playbook

When a user reports an issue:

1. Ask for timestamp and exact action.
2. Ask for request_id shown in UI error (if available).
3. Check backend logs around that request_id.
4. Verify /api/health from the same environment.
5. Re-run backend test suite before deployment.