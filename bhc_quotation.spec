# -*- mode: python ; coding: utf-8 -*-
"""
BHC Quotation Generator — PyInstaller spec file
Build with:  pyinstaller bhc_quotation.spec
"""

import os

ROOT = os.path.abspath(".")

a = Analysis(
    ["run_portable.py"],
    pathex=[ROOT],
    binaries=[],
    datas=[
        # Frontend static files (HTML, JS, CSS) — bundled inside the exe
        (os.path.join(ROOT, "frontend", "bhc"), os.path.join("frontend", "bhc")),
        # Logo — bundled inside the exe so no external data folder needed
        (os.path.join(ROOT, "data", "assets", "quotation_logo.jpg"), os.path.join("data", "assets")),
    ],
    hiddenimports=[
        # FastAPI / uvicorn ecosystem
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "uvicorn.lifespan.off",
        "fastapi",
        "starlette",
        "starlette.responses",
        "starlette.routing",
        "starlette.middleware",
        "starlette.middleware.cors",
        "anyio",
        "anyio._backends",
        "anyio._backends._asyncio",
        "multipart",
        "multipart.multipart",
        # Application modules
        "backend",
        "backend.app",
        "backend.app.main",
        "backend.app.config",
        "backend.app.routes",
        "backend.app.routes.bhc_routes",
        "backend.app.routes.deq_routes",
        "backend.app.services",
        "backend.app.services.bhc_admin_auth",
        "backend.app.services.bhc_config_db",
        "backend.app.services.bhc_excel_reader",
        "backend.app.services.bhc_output_generator",
        "backend.app.services.bhc_pricing_engine",
        "backend.app.services.bhc_workflow_db",
        "backend.app.services.bhc_workflow_service",
        "backend.app.services.deq_output_generator",
        "backend.app.services.deq_db",
        "backend.app.utils",
        "backend.app.utils.paths",
        # Data processing
        "pandas",
        "openpyxl",
        "fpdf",
        "PIL",
        # Misc
        "dotenv",
        "pytz",
        "tzdata",
        "dateutil",
        "email.mime.multipart",
        "email.mime.text",
        "sqlite3",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "scipy",
        "numpy.testing",
        "pytest",
        "IPython",
        "notebook",
        "jupyter",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="BHC_Quotation_Generator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=True,
    icon=None,
)
