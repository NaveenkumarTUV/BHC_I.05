"""
deq_db.py
---------
SQLite storage for Detailed Examination Quotation (DEQ) records.
DEQ records are linked to BHC quotations via bhc_ref_number / bhc_enquiry_id.
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DEQ_REFERENCE_PREFIX = "BEN-DE-TUVR"


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def init_deq_db(db_path: Path) -> None:
    """Ensure the deq_records table exists in the given DB file."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS deq_records (
                id                   TEXT PRIMARY KEY,
                bhc_enquiry_id       TEXT NOT NULL DEFAULT '',
                bhc_ref_number       TEXT NOT NULL DEFAULT '',
                client_name          TEXT NOT NULL DEFAULT '',
                phone                TEXT NOT NULL DEFAULT '',
                property_type        TEXT NOT NULL DEFAULT '',
                area                 REAL NOT NULL DEFAULT 0,
                issue_description    TEXT NOT NULL DEFAULT '',
                examination_type     TEXT NOT NULL DEFAULT 'Structural',
                deq_quoted_amount    REAL NOT NULL DEFAULT 0,
                deq_reference_number TEXT NOT NULL DEFAULT '',
                status               TEXT NOT NULL DEFAULT 'Quoted',
                payment_status       TEXT NOT NULL DEFAULT 'Pending',
                remarks              TEXT NOT NULL DEFAULT '',
                quote_generated_date TEXT NOT NULL DEFAULT '',
                created_at           TEXT NOT NULL DEFAULT '',
                updated_at           TEXT NOT NULL DEFAULT '',
                version              INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        conn.commit()


def format_deq_reference(sequence: int, generated_at: datetime | None = None) -> str:
    """Generate a DEQ reference like BEN-DE-TUVR-20260420-0001."""
    stamp = generated_at or datetime.now()
    return f"{DEQ_REFERENCE_PREFIX}-{stamp.strftime('%Y%m%d')}-{int(sequence):04d}"


def next_deq_sequence_for_date(db_path: Path, date_key: str) -> int:
    init_deq_db(db_path)
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS total FROM deq_records WHERE substr(quote_generated_date, 1, 10) = ?",
            (date_key,),
        ).fetchone()
    return int(row["total"] or 0) + 1


def create_deq_record(db_path: Path, record: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new DEQ record and return it."""
    init_deq_db(db_path)
    now_iso = _utcnow_iso()
    deq_id = str(uuid.uuid4())
    date_key = now_iso[:10]
    seq = next_deq_sequence_for_date(db_path, date_key)
    deq_ref = format_deq_reference(seq, datetime.now())
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO deq_records (
                id, bhc_enquiry_id, bhc_ref_number, client_name, phone,
                property_type, area, issue_description, examination_type,
                deq_quoted_amount, deq_reference_number, status, payment_status,
                remarks, quote_generated_date, created_at, updated_at, version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                deq_id,
                record.get("bhc_enquiry_id", ""),
                record.get("bhc_ref_number", ""),
                record.get("client_name", ""),
                record.get("phone", ""),
                record.get("property_type", ""),
                float(record.get("area", 0) or 0),
                record.get("issue_description", ""),
                record.get("examination_type", "Structural"),
                float(record.get("deq_quoted_amount", 0) or 0),
                deq_ref,
                "Quoted",
                "Pending",
                record.get("remarks", ""),
                date_key,
                now_iso,
                now_iso,
            ),
        )
        conn.commit()
    result = get_deq_record(db_path, deq_id)
    if result is None:
        raise RuntimeError("Failed to create DEQ record.")
    return result


def list_deq_records(db_path: Path) -> List[Dict[str, Any]]:
    init_deq_db(db_path)
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM deq_records ORDER BY quote_generated_date DESC, id DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_deq_record(db_path: Path, deq_id: str) -> Optional[Dict[str, Any]]:
    init_deq_db(db_path)
    with _connect(db_path) as conn:
        row = conn.execute("SELECT * FROM deq_records WHERE id = ?", (deq_id,)).fetchone()
    return dict(row) if row else None


def update_deq_record(
    db_path: Path,
    deq_id: str,
    *,
    status: str | None = None,
    payment_status: str | None = None,
    remarks: str | None = None,
    deq_quoted_amount: float | None = None,
    issue_description: str | None = None,
    examination_type: str | None = None,
) -> bool:
    updates: list[str] = []
    values: list[Any] = []
    if status is not None:
        updates.append("status = ?")
        values.append(status)
    if payment_status is not None:
        updates.append("payment_status = ?")
        values.append(payment_status)
    if remarks is not None:
        updates.append("remarks = ?")
        values.append(remarks)
    if deq_quoted_amount is not None:
        updates.append("deq_quoted_amount = ?")
        values.append(float(deq_quoted_amount))
    if issue_description is not None:
        updates.append("issue_description = ?")
        values.append(issue_description)
    if examination_type is not None:
        updates.append("examination_type = ?")
        values.append(examination_type)
    if not updates:
        return False
    updates.append("updated_at = ?")
    values.append(_utcnow_iso())
    updates.append("version = COALESCE(version, 1) + 1")
    values.append(deq_id)
    init_deq_db(db_path)
    with _connect(db_path) as conn:
        cur = conn.execute(
            f"UPDATE deq_records SET {', '.join(updates)} WHERE id = ?",
            tuple(values),
        )
        conn.commit()
        return cur.rowcount > 0


def delete_deq_record(db_path: Path, deq_id: str) -> bool:
    init_deq_db(db_path)
    with _connect(db_path) as conn:
        cur = conn.execute("DELETE FROM deq_records WHERE id = ?", (deq_id,))
        conn.commit()
        return cur.rowcount > 0


def deq_dashboard_summary(db_path: Path) -> Dict[str, Any]:
    rows = list_deq_records(db_path)
    total = len(rows)
    converted = sum(1 for r in rows if str(r.get("status", "")).lower() == "converted")
    total_revenue = sum(float(r.get("deq_quoted_amount") or 0) for r in rows)
    converted_revenue = sum(
        float(r.get("deq_quoted_amount") or 0)
        for r in rows
        if str(r.get("status", "")).lower() == "converted"
        and str(r.get("payment_status", "")).lower() == "paid"
    )
    return {
        "total": total,
        "converted": converted,
        "total_revenue": float(total_revenue),
        "converted_revenue": float(converted_revenue),
    }
