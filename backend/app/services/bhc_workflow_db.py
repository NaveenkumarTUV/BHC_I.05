"""
bhc_workflow_db.py
------------------
SQLite storage for processed BHC enquiries and quotation status tracking.
"""

import sqlite3
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Optional, Dict, Any, List


WORKFLOW_SCHEMA_VERSION = "2"


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS processed_clients (
                enquiry_id TEXT PRIMARY KEY,
                enquiry_key TEXT UNIQUE,
                client_name TEXT,
                phone TEXT,
                property_type TEXT,
                area REAL,
                quoted_amount REAL,
                reference_number TEXT,
                quote_generated_date TEXT,
                status TEXT,
                payment_status TEXT,
                remarks TEXT,
                timestamp TEXT,
                pincode TEXT DEFAULT ''
            )
            """
        )
        columns = {row[1] for row in conn.execute("PRAGMA table_info(processed_clients)").fetchall()}
        if "reference_number" not in columns:
            conn.execute("ALTER TABLE processed_clients ADD COLUMN reference_number TEXT")
        if "created_at" not in columns:
            conn.execute("ALTER TABLE processed_clients ADD COLUMN created_at TEXT")
            conn.execute("UPDATE processed_clients SET created_at = COALESCE(quote_generated_date, '') WHERE created_at IS NULL")
        if "updated_at" not in columns:
            conn.execute("ALTER TABLE processed_clients ADD COLUMN updated_at TEXT")
            conn.execute("UPDATE processed_clients SET updated_at = COALESCE(quote_generated_date, '') WHERE updated_at IS NULL")
        if "version" not in columns:
            conn.execute("ALTER TABLE processed_clients ADD COLUMN version INTEGER NOT NULL DEFAULT 1")
        if "pincode" not in columns:
            conn.execute("ALTER TABLE processed_clients ADD COLUMN pincode TEXT DEFAULT ''")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS workflow_audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_time TEXT NOT NULL,
                event_type TEXT NOT NULL,
                actor_email TEXT NOT NULL,
                enquiry_id TEXT,
                severity TEXT NOT NULL DEFAULT 'INFO',
                metadata_json TEXT NOT NULL DEFAULT '{}'
            )
            """
        )
        conn.execute(
            "INSERT INTO schema_meta(key, value) VALUES ('workflow_schema_version', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (WORKFLOW_SCHEMA_VERSION,),
        )
        conn.commit()


def get_workflow_schema_version(db_path: Path) -> str:
    init_db(db_path)
    with _connect(db_path) as conn:
        row = conn.execute("SELECT value FROM schema_meta WHERE key = 'workflow_schema_version'").fetchone()
    return str(row["value"]) if row else WORKFLOW_SCHEMA_VERSION


def log_workflow_audit_event(
    db_path: Path,
    event_type: str,
    actor_email: str,
    enquiry_id: str = "",
    severity: str = "INFO",
    metadata: dict[str, Any] | None = None,
) -> None:
    init_db(db_path)
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO workflow_audit_events(
                event_time, event_type, actor_email, enquiry_id, severity, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                _utcnow_iso(),
                str(event_type or "UNKNOWN"),
                str(actor_email or "unknown@system.local"),
                str(enquiry_id or ""),
                str(severity or "INFO").upper(),
                json.dumps(metadata or {}, ensure_ascii=True),
            ),
        )
        conn.commit()


def list_workflow_audit_events(db_path: Path, limit: int = 200) -> List[Dict[str, Any]]:
    safe_limit = max(1, min(int(limit or 200), 1000))
    init_db(db_path)
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, event_time, event_type, actor_email, enquiry_id, severity, metadata_json
            FROM workflow_audit_events
            ORDER BY id DESC
            LIMIT ?
            """,
            (safe_limit,),
        ).fetchall()

    events: List[Dict[str, Any]] = []
    for row in rows:
        raw_meta = str(row["metadata_json"] or "{}")
        try:
            parsed_meta = json.loads(raw_meta)
        except json.JSONDecodeError:
            parsed_meta = {"raw": raw_meta}

        events.append(
            {
                "id": int(row["id"]),
                "event_time": str(row["event_time"]),
                "event_type": str(row["event_type"]),
                "actor_email": str(row["actor_email"]),
                "enquiry_id": str(row["enquiry_id"] or ""),
                "severity": str(row["severity"]),
                "metadata": parsed_meta,
            }
        )

    return events


def upsert_processed_client(db_path: Path, record: Dict[str, Any]) -> str:
    """Insert or update by enquiry_key; returns enquiry_id."""
    enquiry_id = record["enquiry_id"]
    now_iso = _utcnow_iso()
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT enquiry_id FROM processed_clients WHERE enquiry_key = ?",
            (record["enquiry_key"],),
        ).fetchone()

        if row:
            enquiry_id = row["enquiry_id"]
            conn.execute(
                """
                UPDATE processed_clients
                SET client_name = ?,
                    phone = ?,
                    property_type = ?,
                    area = ?,
                    quoted_amount = ?,
                    reference_number = ?,
                    quote_generated_date = ?,
                    status = ?,
                    payment_status = ?,
                    remarks = ?,
                    timestamp = ?,
                    pincode = ?,
                    updated_at = ?,
                    version = COALESCE(version, 1) + 1
                WHERE enquiry_key = ?
                """,
                (
                    record.get("client_name", ""),
                    record.get("phone", ""),
                    record.get("property_type", ""),
                    float(record.get("area", 0) or 0),
                    float(record.get("quoted_amount", 0) or 0),
                    record.get("reference_number", ""),
                    record.get("quote_generated_date", ""),
                    record.get("status", "Quoted"),
                    record.get("payment_status", "Pending"),
                    record.get("remarks", ""),
                    record.get("timestamp", ""),
                    record.get("pincode", ""),
                    now_iso,
                    record.get("enquiry_key", ""),
                ),
            )
        else:
            conn.execute(
                """
                INSERT INTO processed_clients (
                    enquiry_id, enquiry_key, client_name, phone, property_type, area,
                    quoted_amount, reference_number, quote_generated_date, status, payment_status,
                    remarks, timestamp, pincode, created_at, updated_at, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    enquiry_id,
                    record.get("enquiry_key", ""),
                    record.get("client_name", ""),
                    record.get("phone", ""),
                    record.get("property_type", ""),
                    float(record.get("area", 0) or 0),
                    float(record.get("quoted_amount", 0) or 0),
                    record.get("reference_number", ""),
                    record.get("quote_generated_date", ""),
                    record.get("status", "Quoted"),
                    record.get("payment_status", "Pending"),
                    record.get("remarks", ""),
                    record.get("timestamp", ""),
                    record.get("pincode", ""),
                    now_iso,
                    now_iso,
                    1,
                ),
            )
        conn.commit()

    return enquiry_id


def list_processed_clients(db_path: Path) -> List[Dict[str, Any]]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT enquiry_id, enquiry_key, client_name, phone, property_type, area,
                   quoted_amount, reference_number, quote_generated_date, status, payment_status,
                     remarks, timestamp, pincode, created_at, updated_at, version
            FROM processed_clients
            ORDER BY quote_generated_date DESC, enquiry_id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def processed_lookup_by_key(db_path: Path) -> Dict[str, Dict[str, Any]]:
    rows = list_processed_clients(db_path)
    return {str(r.get("enquiry_key", "")): r for r in rows if r.get("enquiry_key")}


def get_processed_client_by_id(db_path: Path, enquiry_id: str) -> Optional[Dict[str, Any]]:
    with _connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT enquiry_id, enquiry_key, client_name, phone, property_type, area,
                   quoted_amount, reference_number, quote_generated_date, status, payment_status,
                     remarks, timestamp, pincode, created_at, updated_at, version
            FROM processed_clients
            WHERE enquiry_id = ?
            """,
            (enquiry_id,),
        ).fetchone()
    return dict(row) if row else None


def get_reference_number_by_key(db_path: Path, enquiry_key: str) -> Optional[str]:
    if not enquiry_key:
        return None

    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT reference_number FROM processed_clients WHERE enquiry_key = ?",
            (enquiry_key,),
        ).fetchone()

    if not row:
        return None

    reference_number = str(row["reference_number"] or "").strip()
    return reference_number or None


def next_quote_sequence_for_date(db_path: Path, date_key: str) -> int:
    with _connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM processed_clients
            WHERE substr(quote_generated_date, 1, 10) = ?
            """,
            (date_key,),
        ).fetchone()

    return int(row["total"] or 0) + 1


def update_client_status(
    db_path: Path,
    enquiry_id: str,
    status: Optional[str] = None,
    payment_status: Optional[str] = None,
    remarks: Optional[str] = None,
) -> bool:
    updates = []
    values = []
    if status is not None:
        updates.append("status = ?")
        values.append(status)
    if payment_status is not None:
        updates.append("payment_status = ?")
        values.append(payment_status)
    if remarks is not None:
        updates.append("remarks = ?")
        values.append(remarks)
    updates.append("updated_at = ?")
    values.append(_utcnow_iso())
    updates.append("version = COALESCE(version, 1) + 1")

    if not updates:
        return False

    values.append(enquiry_id)

    with _connect(db_path) as conn:
        cur = conn.execute(
            f"UPDATE processed_clients SET {', '.join(updates)} WHERE enquiry_id = ?",
            tuple(values),
        )
        conn.commit()
        return cur.rowcount > 0


def dashboard_summary(db_path: Path, total_enquiries: int, pending: int) -> Dict[str, Any]:
    rows = list_processed_clients(db_path)
    quoted = len(rows)
    converted = sum(1 for r in rows if str(r.get("status", "")).lower() == "converted")
    quoted_revenue = sum(float(r.get("quoted_amount") or 0) for r in rows)
    converted_revenue = sum(
        float(r.get("quoted_amount") or 0)
        for r in rows
        if str(r.get("status", "")).lower() == "converted"
    )
    return {
        "total_enquiries": int(total_enquiries),
        "pending": int(pending),
        "quoted": int(quoted),
        "converted": int(converted),
        "quoted_revenue": float(quoted_revenue),
        "converted_revenue": float(converted_revenue),
        # Backward-compatible alias retained for older clients.
        "revenue": float(quoted_revenue),
    }
