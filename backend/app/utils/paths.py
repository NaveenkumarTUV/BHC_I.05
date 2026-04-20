import sys
from datetime import datetime
from pathlib import Path

# Load environment variables
from backend.app.config import DATA_DIR_PATH, EXPORTS_BASE_PATH


def get_base_path():
    """
    Get the base directory for bundled resources.
    When frozen by PyInstaller, sys._MEIPASS contains the temp extraction folder.
    Otherwise, return the project root directory.
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled executable - return the temp extraction path
        return Path(sys._MEIPASS)
    else:
        # Running as script - return project root above backend/app/
        return Path(__file__).resolve().parents[3]


def get_data_dir():
    """
    Get the data directory (always external, never bundled).
    Returns the configured data folder or falls back to local 'data' folder.
    If the configured path is on an unreachable network drive, falls back silently.
    """
    def _local_fallback():
        if getattr(sys, 'frozen', False):
            exe_dir = Path(sys.executable).parent
        else:
            exe_dir = get_base_path()
        local = exe_dir / "data"
        local.mkdir(parents=True, exist_ok=True)
        return local

    # Use DATA_DIR_PATH from environment if configured
    if DATA_DIR_PATH:
        data_path = Path(DATA_DIR_PATH)
        try:
            if not data_path.exists():
                data_path.mkdir(parents=True, exist_ok=True)
            return data_path
        except (OSError, FileNotFoundError) as e:
            import warnings
            warnings.warn(
                f"Configured DATA_DIR_PATH '{DATA_DIR_PATH}' is inaccessible ({e}). "
                f"Falling back to local 'data' directory.",
                RuntimeWarning,
                stacklevel=2,
            )
            return _local_fallback()

    return _local_fallback()


# Base directories - bundled resources use get_base_path(), data files use get_data_dir()
BASE_DIR = get_base_path()
APP_DIR = BASE_DIR / "backend" / "app"
DATA_DIR = get_data_dir()
FRONTEND_DIR = BASE_DIR / "frontend"
EXPORTS_DIR = DATA_DIR / "exports"


def _resolve_exports_base() -> Path:
    """
    Return the base exports directory.
    Uses EXPORTS_BASE_PATH from .env if set and reachable,
    otherwise falls back to DATA_DIR/exports.
    """
    if EXPORTS_BASE_PATH:
        p = Path(EXPORTS_BASE_PATH)
        try:
            p.mkdir(parents=True, exist_ok=True)
            return p
        except (OSError, FileNotFoundError):
            import warnings
            warnings.warn(
                f"EXPORTS_BASE_PATH '{EXPORTS_BASE_PATH}' is inaccessible. "
                f"Falling back to local exports directory.",
                RuntimeWarning,
                stacklevel=2,
            )
    return EXPORTS_DIR


def get_dated_export_dir(module: str) -> Path:
    """
    Return an export directory organised by year and month.
    Example: <exports_base>/<module>/2026/04/
    Directories are created automatically.
    """
    now = datetime.now()
    target = _resolve_exports_base() / module / str(now.year) / f"{now.month:02d}"
    target.mkdir(parents=True, exist_ok=True)
    return target


def ensure_dir(path: Path) -> Path:
    """Create a directory if it does not exist and return the path."""
    path.mkdir(parents=True, exist_ok=True)
    return path
