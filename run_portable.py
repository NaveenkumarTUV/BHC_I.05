"""
run_portable.py
---------------
Entry point for the PyInstaller-built executable.
Starts the FastAPI/uvicorn server and opens the browser automatically.
"""

import multiprocessing
import sys
import os
import webbrowser
import threading
import time
import socket


def _port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


def _open_browser(port: int) -> None:
    """Wait until the server is accepting connections, then open browser."""
    for _ in range(30):
        time.sleep(0.5)
        if not _port_available(port):
            webbrowser.open(f"http://127.0.0.1:{port}/bhc")
            return


def main() -> None:
    # Required for PyInstaller on Windows to avoid recursive process spawning
    multiprocessing.freeze_support()

    port = 7860

    # Open browser in a background thread once the server is ready
    threading.Thread(target=_open_browser, args=(port,), daemon=True).start()

    # Import and run the app
    import uvicorn
    from backend.app.main import app

    print(f"\n  ========================================")
    print(f"  BHC Quotation Generator is now running.")
    print(f"  Opening browser at http://127.0.0.1:{port}/bhc")
    print(f"  Press Ctrl+C to stop.")
    print(f"  ========================================\n")

    # Suppress uvicorn access logs (every request) — only show warnings & errors
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {"format": "%(asctime)s  %(levelname)s  %(message)s", "datefmt": "%H:%M:%S"},
        },
        "handlers": {
            "console": {"class": "logging.StreamHandler", "formatter": "simple"},
        },
        "loggers": {
            "uvicorn": {"handlers": ["console"], "level": "WARNING", "propagate": False},
            "uvicorn.error": {"handlers": ["console"], "level": "WARNING", "propagate": False},
            "uvicorn.access": {"handlers": [], "level": "CRITICAL", "propagate": False},
            "bhc.app": {"handlers": ["console"], "level": "WARNING", "propagate": False},
            "bhc.output": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        },
        "root": {"handlers": ["console"], "level": "WARNING"},
    }

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning", log_config=log_config)


if __name__ == "__main__":
    main()
