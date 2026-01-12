import pandas as pd
from pathlib import Path

# =========================
# Load PIN reference
# =========================
def load_pin_reference(pin_ref_file: Path):
    """
    Load authoritative PIN → district/state mapping from CSV.
    """

    ref = pd.read_csv(pin_ref_file)

    # Normalize column names
    ref.columns = ref.columns.str.lower().str.strip()

    # Validate required columns (based on your actual schema)
    required_cols = {"pincode", "district", "statename"}
    missing = required_cols - set(ref.columns)
    if missing:
        raise ValueError(f"Reference file missing required columns: {missing}")

    # Normalize PIN
    ref["pincode"] = ref["pincode"].astype(str).str.zfill(6)

    # Normalize text
    ref["district"] = ref["district"].astype(str).str.strip().str.upper()
    ref["state"] = ref["statename"].astype(str).str.strip().str.upper()

    # Keep optional geo columns if present
    geo_cols = []
    if "latitude" in ref.columns:
        geo_cols.append("latitude")
    if "longitude" in ref.columns:
        geo_cols.append("longitude")

    # Final reference table used for merging
    ref = ref[["pincode", "district", "state"] + geo_cols]

    return ref


# =========================
# Apply normalization
# =========================
def normalize_geo(df: pd.DataFrame, pin_ref: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize district and state using authoritative PIN reference.
    Raw district/state values in df are ignored.
    """

    # Ensure PIN format
    df["pincode"] = df["pincode"].astype(str).str.zfill(6)

    # Merge with reference
    df = df.merge(
        pin_ref,
        on="pincode",
        how="left",
        suffixes=("", "_ref")
    )

    # Replace geography from reference
    df["district"] = df["district_ref"]
    df["state"] = df["state_ref"]

    # Mapping audit column
    df["geo_mapping_status"] = df["district"].notna().map(
        {True: "MAPPED", False: "UNMAPPED"}
    )

    # Safety fallback
    df["district"] = df["district"].fillna("UNKNOWN")
    df["state"] = df["state"].fillna("UNKNOWN")

    # Drop helper columns
    df.drop(
        columns=[c for c in df.columns if c.endswith("_ref")],
        inplace=True
    )

    return df
