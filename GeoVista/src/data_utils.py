"""
data_utils.py
-------------
CSV validation, loading, and preprocessing for GeoVista.
"""

import pandas as pd
import streamlit as st

REQUIRED_COLUMNS = {"latitude", "longitude"}
OPTIONAL_COLUMNS = {
    "project_name", "type", "cost_crore", "status", "district", "year", "project_id"
}


def validate_csv(df: pd.DataFrame) -> tuple[bool, str]:
    """
    Validate uploaded DataFrame for required columns and data integrity.
    Returns (is_valid, error_message).
    """
    missing = REQUIRED_COLUMNS - set(df.columns.str.lower())
    if missing:
        return False, f"Missing required columns: {', '.join(missing)}. CSV must contain 'latitude' and 'longitude'."

    df.columns = df.columns.str.lower()

    try:
        df["latitude"] = pd.to_numeric(df["latitude"], errors="raise")
        df["longitude"] = pd.to_numeric(df["longitude"], errors="raise")
    except Exception:
        return False, "Columns 'latitude' and 'longitude' must contain numeric values."

    invalid_lat = df[(df["latitude"] < -90) | (df["latitude"] > 90)]
    invalid_lon = df[(df["longitude"] < -180) | (df["longitude"] > 180)]
    if not invalid_lat.empty or not invalid_lon.empty:
        return False, "Some coordinates are out of valid range (lat: -90 to 90, lon: -180 to 180)."

    null_coords = df[df["latitude"].isnull() | df["longitude"].isnull()]
    if not null_coords.empty:
        return False, f"{len(null_coords)} rows have missing coordinates and will be dropped."

    return True, ""


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardise column names, drop nulls, fill optional columns with defaults.
    """
    df = df.copy()
    df.columns = df.columns.str.lower().str.strip()

    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df.dropna(subset=["latitude", "longitude"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Fill optional columns with sensible defaults
    defaults = {
        "project_name": "Unnamed Project",
        "type": "Unknown",
        "cost_crore": 0,
        "status": "Unknown",
        "district": "Unknown",
        "year": "N/A",
        "project_id": [f"P{str(i+1).zfill(3)}" for i in range(len(df))],
    }
    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default if not isinstance(default, list) else default

    df["cost_crore"] = pd.to_numeric(df["cost_crore"], errors="coerce").fillna(0)

    return df


def load_sample_data() -> pd.DataFrame:
    """Load the bundled Tamil Nadu AEC sample dataset."""
    import os
    sample_path = os.path.join(os.path.dirname(__file__), "..", "data", "sample_data.csv")
    df = pd.read_csv(sample_path)
    return preprocess(df)


def summary_stats(df: pd.DataFrame) -> dict:
    """Return key summary statistics for the sidebar."""
    stats = {
        "total_projects": len(df),
        "total_cost_crore": df["cost_crore"].sum(),
        "project_types": df["type"].nunique() if "type" in df.columns else "N/A",
        "districts": df["district"].nunique() if "district" in df.columns else "N/A",
        "status_counts": df["status"].value_counts().to_dict() if "status" in df.columns else {},
    }
    return stats
