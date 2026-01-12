# import pandas as pd
# from pathlib import Path

# # =========================
# # Paths
# # =========================
# PROCESSED_DIR = Path("data/processed")
# REFERENCE_DIR = Path("data/reference")

# PIN_REF_FILE = REFERENCE_DIR / "pin_district.csv"

# # Load reference mapping
# def load_pin_reference():
#     """
#     Load authoritative PIN → district/state mapping
#     """
#     ref = pd.read_csv(PIN_REF_FILE, low_memory=False)

#     # Normalize column names
#     ref.columns = ref.columns.str.lower().str.strip()

#     # ✅ Accept statename instead of state
#     required_cols = {"pincode", "district", "statename"}
#     missing = required_cols - set(ref.columns)
#     if missing:
#         raise ValueError(f"Reference file missing columns: {missing}")

#     # Normalize PIN
#     ref["pincode"] = ref["pincode"].astype(str).str.zfill(6)

#     # Normalize text
#     ref["district"] = ref["district"].astype(str).str.strip().str.upper()
#     ref["state"] = ref["statename"].astype(str).str.strip().str.upper()

#     # Keep optional geo columns if present
#     geo_cols = []
#     if "latitude" in ref.columns:
#         geo_cols.append("latitude")
#     if "longitude" in ref.columns:
#         geo_cols.append("longitude")

#     # Select only required columns for merge
#     ref = ref[["pincode", "district", "state"] + geo_cols]

#     return ref
    
# # Geography normalization
# def normalize_geo_using_reference(df, pin_ref):
#     """
#     Replace district/state using authoritative PIN reference
#     """

#     df["pincode"] = df["pincode"].astype(str).str.zfill(6)

#     # Merge with reference
#     df = df.merge(
#         pin_ref,
#         on="pincode",
#         how="left",
#         suffixes=("", "_ref")
#     )

#     # Replace geography ONLY from reference
#     df["district"] = df["district_ref"]
#     df["state"] = df["state_ref"]

#     # Optional geo columns (if present in reference)
#     if "latitude_ref" in df.columns:
#         df["latitude"] = df["latitude_ref"]
#     if "longitude_ref" in df.columns:
#         df["longitude"] = df["longitude_ref"]

#     # Track unmapped PINs
#     df["geo_mapping_status"] = df["district"].notna().map(
#         {True: "MAPPED", False: "UNMAPPED"}
#     )

#     # Safety fallback
#     df["district"] = df["district"].fillna("UNKNOWN")
#     df["state"] = df["state"].fillna("UNKNOWN")

#     # Drop helper columns
#     df.drop(
#         columns=[c for c in df.columns if c.endswith("_ref")],
#         inplace=True
#     )

#     return df


# # Dataset cleaners

# def clean_enrolment(pin_ref):
#     print("[INFO] Cleaning ENROLMENT data")

#     df = pd.read_csv(PROCESSED_DIR / "enrolment_raw_all.csv")
#     df.columns = df.columns.str.lower().str.strip()

#     df.rename(columns={"date": "enrolment_date"}, inplace=True)
#     df["enrolment_date"] = pd.to_datetime(df["enrolment_date"], errors="coerce")

#     df = normalize_geo_using_reference(df, pin_ref)

#     df = df.dropna(subset=["enrolment_date", "pincode"])

#     df.to_csv(PROCESSED_DIR / "enrolment_clean.csv", index=False)
#     print("[SUCCESS] Enrolment cleaned using PIN reference")


# def clean_demographic(pin_ref):
#     print("[INFO] Cleaning DEMOGRAPHIC data")

#     df = pd.read_csv(PROCESSED_DIR / "demographic_raw_all.csv")
#     df.columns = df.columns.str.lower().str.strip()

#     df.rename(columns={"date": "update_date"}, inplace=True)
#     df["update_date"] = pd.to_datetime(df["update_date"], errors="coerce")

#     df = normalize_geo_using_reference(df, pin_ref)

#     df = df.dropna(subset=["update_date", "pincode"])

#     df.to_csv(PROCESSED_DIR / "demographic_clean.csv", index=False)
#     print("[SUCCESS] Demographic cleaned using PIN reference")


# def clean_biometric(pin_ref):
#     print("[INFO] Cleaning BIOMETRIC data")

#     df = pd.read_csv(PROCESSED_DIR / "biometric_raw_all.csv")
#     df.columns = df.columns.str.lower().str.strip()

#     df.rename(columns={"date": "update_date"}, inplace=True)
#     df["update_date"] = pd.to_datetime(df["update_date"], errors="coerce")

#     df = normalize_geo_using_reference(df, pin_ref)

#     df = df.dropna(subset=["update_date", "pincode"])

#     df.to_csv(PROCESSED_DIR / "biometric_clean.csv", index=False)
#     print("[SUCCESS] Biometric cleaned using PIN reference")


# # Entry point

# if __name__ == "__main__":
#     print("========== STARTING CLEANUP ==========")

#     pin_ref = load_pin_reference()

#     clean_enrolment(pin_ref)
#     clean_demographic(pin_ref)
#     clean_biometric(pin_ref)

#     print("========== CLEANUP COMPLETED ==========")
