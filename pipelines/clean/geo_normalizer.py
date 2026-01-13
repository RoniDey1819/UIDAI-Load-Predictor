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
# Apply normalization (UPDATED)
# =========================
def normalize_geo(df: pd.DataFrame, pin_ref: pd.DataFrame) -> pd.DataFrame:
    pin_to_district = pin_ref.set_index("pincode")["district"]
    pin_to_state = pin_ref.set_index("pincode")["state"]

    df["pincode"] = df["pincode"].astype(str).str.zfill(6)

    # --- Preserve raw geography BEFORE overwrite ---
    df["district_raw"] = df.get("district")
    df["state_raw"] = df.get("state")

    # --- PIN-based mapping ---
    district_pin = df["pincode"].map(pin_to_district)
    state_pin = df["pincode"].map(pin_to_state)

    # --- Raw fallback (normalized text) ---
    district_raw = (
        df["district_raw"]
        .astype(str)
        .str.strip()
        .str.upper()
        .replace({"": None, "NAN": None})
    )

    state_raw = (
        df["state_raw"]
        .astype(str)
        .str.strip()
        .str.upper()
        .replace({"": None, "NAN": None})
    )

    # --- Final resolved geography (PIN → fallback) ---
    df["district"] = district_pin.combine_first(district_raw)
    df["state"] = state_pin.combine_first(state_raw)

    # --- Mapping status ---
    df["geo_mapping_status"] = df["district"].notna().map(
        {True: "MAPPED", False: "UNMAPPED"}
    )

    # --- Final safety fallback ---
    df["district"] = df["district"].fillna("UNKNOWN")
    df["state"] = df["state"].fillna("UNKNOWN")

    # Cleanup helper columns
    df.drop(columns=["district_raw", "state_raw"], inplace=True)

    return df
