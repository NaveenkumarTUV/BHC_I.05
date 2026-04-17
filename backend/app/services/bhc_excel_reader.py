"""
bhc_excel_reader.py
-------------------
Reads Microsoft Form response Excel file and returns structured client data.
Columns expected:
    Client_Name, Phone_Number, Client_Email, Location, Property_Type,
    Building_System, Area_sqft, Issue_Observed, Building_Age, Urgency,
    GST_Number, PAN_Number, Notes
"""

import pandas as pd
import re
from pathlib import Path
from typing import List, Dict, Any

EXPECTED_COLUMNS = [
    "Timestamp",
    "Client_Name",
    "Phone_Number",
    "Client_Email",
    "Location",
    "Property_Type",
    "Building_System",
    "Area_sqft",
    "Issue_Observed",
    "Building_Age",
    "Urgency",
    "GST_Number",
    "PAN_Number",
    "Notes",
]


def _detect_building_system(value: str) -> str:
    """Normalize free-text form answers to rcc/steel/both when possible."""
    text = str(value or "").strip().lower()
    if not text:
        return ""

    has_rcc = any(token in text for token in ["rcc", "rc", "reinforced concrete", "reinforced cement concrete"])
    has_steel = any(token in text for token in ["steel", "structural steel", "steel structure"])
    has_combined = any(token in text for token in ["both", "combined", "combined structure", "composite", "rcc + peb", "rcc+peb"])

    if has_combined or (has_rcc and has_steel):
        return "Both"
    if has_rcc:
        return "RCC"
    if has_steel:
        return "Steel"
    return ""


def _infer_building_system_from_record(record: Dict[str, Any]) -> str:
    """
    Infer building system from canonical and non-canonical form columns.
    This supports evolving Microsoft Form question labels without code changes.
    """
    direct = _detect_building_system(record.get("Building_System", ""))
    if direct:
        return direct

    for key, value in record.items():
        key_lower = str(key or "").strip().lower()
        if any(token in key_lower for token in ["building system", "structural system", "structure", "scope"]):
            detected = _detect_building_system(value)
            if detected:
                return detected

    for key in ("Property_Type", "Issue_Observed", "Notes"):
        detected = _detect_building_system(record.get(key, ""))
        if detected:
            return detected

    return ""

# Column aliases – maps alternative names from real Microsoft Form exports to canonical names
COLUMN_ALIASES: Dict[str, str] = {
    "timestamp":         "Timestamp",
    "submitted at":      "Timestamp",
    "submission time":   "Timestamp",
    "start time":        "Timestamp",
    "completion time":   "Timestamp",
    "name":              "Client_Name",
    "full name":         "Client_Name",
    "full name (as per form)": "Client_Name",
    "client name":       "Client_Name",
    "full name / company name": "Client_Name",
    "phone number":      "Phone_Number",
    "phone":             "Phone_Number",
    "mobile":            "Phone_Number",
    "mobile number":     "Phone_Number",
    "contact":           "Phone_Number",
    "contact number":    "Phone_Number",
    "email":             "Client_Email",
    "email1":            "Client_Email",
    "email address":     "Client_Email",
    "client email":      "Client_Email",
    "address":           "Location",
    "city":              "Location",
    "location (city / site address)": "Location",
    "complete adress":   "Location",
    "complete address":  "Location",
    "property type":     "Property_Type",
    "type":              "Property_Type",
    "building system":   "Building_System",
    "structure type":    "Building_System",
    "type of structure": "Building_System",
    "structural system": "Building_System",
    "building type":     "Building_System",
    "building system (rcc/steel/both)": "Building_System",
    "which building system is applicable": "Building_System",
    "scope selection": "Building_System",
    "scope type": "Building_System",
    "area":              "Area_sqft",
    "approximate area":  "Area_sqft",
    "area (sqft)":       "Area_sqft",
    "area_sq.ft":        "Area_sqft",
    "sqft":              "Area_sqft",
    "builtup area":      "Area_sqft",
    "issues":            "Issue_Observed",
    "issues observed":   "Issue_Observed",
    "issue":             "Issue_Observed",
    "do you notice any issues?": "Issue_Observed",
    "problem":           "Issue_Observed",
    "age":               "Building_Age",
    "building age":      "Building_Age",
    "age (years)":       "Building_Age",
    "year of construction": "Building_Age",
    "remark":            "Notes",
    "remarks":           "Notes",
    "additional notes":  "Notes",
    "description":       "Notes",
    "urgency":           "Urgency",
    "when do you need this": "Urgency",
    "when do you need this?": "Urgency",
    "when do u need this inspection?": "Urgency",
    "when do u need this inspection": "Urgency",
    "timeline":          "Urgency",
    "when needed":       "Urgency",
    "priority":          "Urgency",
    "service urgency":   "Urgency",
    "do you have gst number?": "GST_Number",
    "enter gst number":  "GST_Number",
    "gst number":        "GST_Number",
    "gst":               "GST_Number",
    "gst no":            "GST_Number",
    "gstin":             "GST_Number",
    "do you have pan number?": "PAN_Number",
    "enter pan number":  "PAN_Number",
    "pan number":        "PAN_Number",
    "pan":               "PAN_Number",
    "pan no":            "PAN_Number",
}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename DataFrame columns to canonical names using aliases."""
    rename_map: Dict[str, str] = {}
    for col in df.columns:
        lower = col.strip().lower()
        if lower in COLUMN_ALIASES:
            rename_map[col] = COLUMN_ALIASES[lower]
    if rename_map:
        df = df.rename(columns=rename_map)
    return df


def read_clients_from_excel(filepath: Path) -> List[Dict[str, Any]]:
    """
    Read all rows from the Excel file.
    Returns a list of dicts with canonical keys + a computed _area_numeric float.
    Raises FileNotFoundError if the file does not exist.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Enquiry Excel file not found: {filepath}")

    df = pd.read_excel(filepath, dtype=str)
    df = df.where(df.notna(), other="")   # replace NaN with empty string
    df.columns = [str(c).strip() for c in df.columns]
    df = _normalize_columns(df)
    # Forms exports can produce duplicate logical headers after alias-normalization
    # (e.g., Name + Full Name both mapped to Client_Name). Merge them row-wise by
    # taking the first non-empty value, then keep a single final column.
    if df.columns.duplicated().any():
        merged = {}
        for col in dict.fromkeys(df.columns):
            same = df.loc[:, df.columns == col]
            if same.shape[1] == 1:
                merged[col] = same.iloc[:, 0]
            else:
                merged[col] = same.replace("", pd.NA).bfill(axis=1).iloc[:, 0].fillna("")
        df = pd.DataFrame(merged)

    # Add any missing expected columns as empty strings
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    records: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        record: Dict[str, Any] = {col: str(row.get(col, "")).strip() for col in df.columns}
        inferred_system = _infer_building_system_from_record(record)
        if inferred_system:
            record["Building_System"] = inferred_system
        # Compute numeric area for the pricing engine
        try:
            record["_area_numeric"] = float(record.get("Area_sqft", 0) or 0)
        except ValueError:
            area_text = str(record.get("Area_sqft", "")).replace(",", "")
            nums = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", area_text)]
            record["_area_numeric"] = max(nums) if nums else 0.0
        records.append(record)

    return records
