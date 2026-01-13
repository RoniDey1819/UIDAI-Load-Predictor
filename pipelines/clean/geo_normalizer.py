import pandas as pd
from pathlib import Path

# =========================
# Load PIN reference
# =========================
def load_pin_reference(pin_ref_file: Path):
    ref = pd.read_csv(pin_ref_file)

    ref.columns = ref.columns.str.lower().str.strip()

    required_cols = {"pincode", "district", "statename"}
    missing = required_cols - set(ref.columns)
    if missing:
        raise ValueError(f"Reference file missing required columns: {missing}")

    ref["pincode"] = ref["pincode"].astype(str).str.zfill(6)

    ref["district"] = ref["district"].astype(str).str.strip().str.upper()
    ref["state"] = ref["statename"].astype(str).str.strip().str.upper()

    # 🚨 CRITICAL: enforce one row per PIN
    ref = (
        ref.sort_values(["pincode"])
           .drop_duplicates(subset=["pincode"], keep="first")
           .reset_index(drop=True)
    )

    return ref[["pincode", "district", "state"]]



# =========================
# Apply normalization
# =========================
def normalize_geo(df: pd.DataFrame, pin_ref: pd.DataFrame) -> pd.DataFrame:
    pin_to_district = pin_ref.set_index("pincode")["district"]
    pin_to_state = pin_ref.set_index("pincode")["state"]

    df["pincode"] = df["pincode"].astype(str).str.zfill(6)

    df["district"] = df["pincode"].map(pin_to_district)
    df["state"] = df["pincode"].map(pin_to_state)

    df["geo_mapping_status"] = df["district"].notna().map(
        {True: "MAPPED", False: "UNMAPPED"}
    )

    df["district"] = df["district"].fillna("UNKNOWN")
    df["state"] = df["state"].fillna("UNKNOWN")

    return df
