# import pandas as pd
# from pathlib import Path

# from .geo_normalizer import load_pin_reference
# from .enrolment import clean_enrolment
# from .demographic import clean_demographic
# from .biometric import clean_biometric

# PROCESSED = Path("data/processed")
# PIN_REF = Path("data/reference/pin_district.csv")


# def run():
#     print("========== STARTING CLEANUP ==========")

#     PROCESSED.mkdir(parents=True, exist_ok=True)

#     status = {
#         "ENROLMENT": "NOT RUN",
#         "DEMOGRAPHIC": "NOT RUN",
#         "BIOMETRIC": "NOT RUN"
#     }

#     try:
#         pin_ref = load_pin_reference(PIN_REF)
#         print("[INFO] PIN reference loaded successfully")
#     except Exception as e:
#         print("[FATAL] Failed to load PIN reference")
#         print(f"Reason: {e}")
#         return

#     # -------------------------
#     # ENROLMENT
#     # -------------------------
#     print("\n[START] ENROLMENT cleaning")
#     try:
#         df = pd.read_csv(PROCESSED / "enrolment_raw_all.csv")
#         out_path = PROCESSED / "enrolment_clean.csv"

#         clean_enrolment(df, pin_ref).to_csv(out_path, index=False)

#         print(f"[SUCCESS] ENROLMENT cleaned → {out_path}")
#         status["ENROLMENT"] = "SUCCESS"
#     except Exception as e:
#         print("[FAILED] ENROLMENT cleaning")
#         print(f"Reason: {e}")
#         status["ENROLMENT"] = "FAILED"

#     # -------------------------
#     # DEMOGRAPHIC
#     # -------------------------
#     print("\n[START] DEMOGRAPHIC cleaning")
#     try:
#         df = pd.read_csv(PROCESSED / "demographic_raw_all.csv")
#         out_path = PROCESSED / "demographic_clean.csv"

#         clean_demographic(df, pin_ref).to_csv(out_path, index=False)

#         print(f"[SUCCESS] DEMOGRAPHIC cleaned → {out_path}")
#         status["DEMOGRAPHIC"] = "SUCCESS"
#     except Exception as e:
#         print("[FAILED] DEMOGRAPHIC cleaning")
#         print(f"Reason: {e}")
#         status["DEMOGRAPHIC"] = "FAILED"

#     # -------------------------
#     # BIOMETRIC
#     # -------------------------
#     print("\n[START] BIOMETRIC cleaning")
#     try:
#         df = pd.read_csv(PROCESSED / "biometric_raw_all.csv")
#         out_path = PROCESSED / "biometric_clean.csv"

#         clean_biometric(df, pin_ref).to_csv(out_path, index=False)

#         print(f"[SUCCESS] BIOMETRIC cleaned → {out_path}")
#         status["BIOMETRIC"] = "SUCCESS"
#     except Exception as e:
#         print("[FAILED] BIOMETRIC cleaning")
#         print(f"Reason: {e}")
#         status["BIOMETRIC"] = "FAILED"

#     # -------------------------
#     # SUMMARY
#     # -------------------------
#     print("\n========== CLEANUP SUMMARY ==========")
#     for k, v in status.items():
#         print(f"{k:<12}: {v}")
#     print("====================================")


# if __name__ == "__main__":
#     run()



#chunked

from pathlib import Path
import hashlib

from .geo_normalizer import load_pin_reference
from .enrolment import clean_enrolment
from .demographic import clean_demographic
from .biometric import clean_biometric
from .chunk_runner import process_csv_with_fallback


# =========================
# Paths
# =========================
PROCESSED = Path("data/processed")
REFERENCE = Path("data/reference/pin_district.csv")


# =========================
# Verification utilities
# =========================
def count_rows(path: Path) -> int:
    """Fast row count without loading full CSV"""
    with open(path, "r", encoding="utf-8") as f:
        return sum(1 for _ in f) - 1  # exclude header


def file_row_hashes(path: Path) -> set:
    """
    Generate a hash for every row (excluding header).
    Used to detect artificial duplication or loss.
    """
    hashes = set()
    with open(path, "r", encoding="utf-8") as f:
        next(f)  # skip header
        for line in f:
            hashes.add(hashlib.md5(line.encode()).hexdigest())
    return hashes


def verify_row_integrity(raw_path: Path, clean_path: Path, dataset_name: str):
    """
    Verifies cleaning integrity:
    1. Raw row count == Clean row count
    Cleaning is allowed to change content, not cardinality.
    """

    def count_rows(path):
        with open(path, "r", encoding="utf-8") as f:
            return sum(1 for _ in f) - 1  # exclude header

    raw_rows = count_rows(raw_path)
    clean_rows = count_rows(clean_path)

    print(f"\n[VERIFY] {dataset_name}")
    print(f"  Raw rows   : {raw_rows:,}")
    print(f"  Clean rows : {clean_rows:,}")

    if raw_rows != clean_rows:
        raise ValueError(
            f"[ERROR] Row count mismatch for {dataset_name}: "
            f"{raw_rows} → {clean_rows}"
        )

    print(f"[OK] {dataset_name} row integrity verified")



# =========================
# Main runner (UNCHANGED FLOW)
# =========================
def run():
    print("========== STARTING CLEANUP ==========")

    PROCESSED.mkdir(parents=True, exist_ok=True)

    # Load PIN reference
    pin_ref = load_pin_reference(REFERENCE)
    print("[INFO] PIN reference loaded")

    # -------------------------
    # ENROLMENT
    # -------------------------
    print("\n[START] ENROLMENT")
    process_csv_with_fallback(
        input_path=PROCESSED / "enrolment_raw_all.csv",
        output_path=PROCESSED / "enrolment_clean.csv",
        clean_fn=clean_enrolment,
        pin_ref=pin_ref
    )

    verify_row_integrity(
        raw_path=PROCESSED / "enrolment_raw_all.csv",
        clean_path=PROCESSED / "enrolment_clean.csv",
        dataset_name="ENROLMENT"
    )

    # -------------------------
    # DEMOGRAPHIC
    # -------------------------
    print("\n[START] DEMOGRAPHIC")
    process_csv_with_fallback(
        input_path=PROCESSED / "demographic_raw_all.csv",
        output_path=PROCESSED / "demographic_clean.csv",
        clean_fn=clean_demographic,
        pin_ref=pin_ref
    )

    verify_row_integrity(
        raw_path=PROCESSED / "demographic_raw_all.csv",
        clean_path=PROCESSED / "demographic_clean.csv",
        dataset_name="DEMOGRAPHIC"
    )

    # -------------------------
    # BIOMETRIC
    # -------------------------
    print("\n[START] BIOMETRIC")
    process_csv_with_fallback(
        input_path=PROCESSED / "biometric_raw_all.csv",
        output_path=PROCESSED / "biometric_clean.csv",
        clean_fn=clean_biometric,
        pin_ref=pin_ref
    )

    verify_row_integrity(
        raw_path=PROCESSED / "biometric_raw_all.csv",
        clean_path=PROCESSED / "biometric_clean.csv",
        dataset_name="BIOMETRIC"
    )

    print("\n========== CLEANUP COMPLETED SUCCESSFULLY ==========")


if __name__ == "__main__":
    run()


