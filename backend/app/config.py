"""Application configuration for the BHC quotation workflow."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv, set_key


def _resolve_config_file() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / ".env"

    repo_root = Path(__file__).resolve().parents[2]
    backend_root = Path(__file__).resolve().parents[1]

    for candidate in (repo_root / ".env", backend_root / ".env"):
        if candidate.exists():
            return candidate

    return repo_root / ".env"


CONFIG_FILE = _resolve_config_file()
load_dotenv(CONFIG_FILE)


def get_env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def get_bool_env(key: str, default: bool) -> bool:
    return get_env(key, str(default).lower()).strip().lower() == "true"


def get_int_env(key: str, default: int) -> int:
    raw_value = get_env(key, str(default)).strip()
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"Environment variable '{key}' must be an integer. Got: '{raw_value}'") from exc


def set_env_value(key: str, value: str) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        CONFIG_FILE.touch()
    set_key(str(CONFIG_FILE), key, value, quote_mode="never")
    os.environ[key] = value


SERVER_HOST = get_env("SERVER_HOST", "127.0.0.1")
SERVER_PORT = get_int_env("SERVER_PORT", 7860)
DEBUG_MODE = get_bool_env("DEBUG_MODE", False)

DATA_DIR_PATH = get_env("DATA_DIR_PATH", "")
EXCEL_FILE_PATH = get_env("EXCEL_FILE_PATH", "")
BHC_PROCESSED_DB_PATH = get_env("BHC_PROCESSED_DB_PATH", "")
BHC_CONFIG_DB_PATH = get_env("BHC_CONFIG_DB_PATH", "")
BHC_ADMIN_PASSWORD = get_env("BHC_ADMIN_PASSWORD", "")
ALLOWED_ORIGINS = [o.strip() for o in get_env("ALLOWED_ORIGINS", f"http://127.0.0.1:{SERVER_PORT},http://localhost:{SERVER_PORT}").split(",") if o.strip()]


def validate_runtime_config() -> None:
    """Validate runtime settings early so misconfiguration fails fast."""
    errors: list[str] = []

    if not (1 <= SERVER_PORT <= 65535):
        errors.append("SERVER_PORT must be between 1 and 65535.")

    if SERVER_HOST.strip() == "":
        errors.append("SERVER_HOST cannot be empty.")

    for env_name, env_value in (
        ("BHC_PROCESSED_DB_PATH", BHC_PROCESSED_DB_PATH),
        ("BHC_CONFIG_DB_PATH", BHC_CONFIG_DB_PATH),
        ("EXCEL_FILE_PATH", EXCEL_FILE_PATH),
    ):
        candidate = env_value.strip()
        if not candidate:
            continue
        try:
            Path(candidate)
        except Exception as exc:  # pragma: no cover - defensive validation
            errors.append(f"{env_name} is not a valid path: {exc}")

    if errors:
        raise ValueError("Invalid runtime configuration: " + " | ".join(errors))
