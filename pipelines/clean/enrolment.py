# pipelines/clean/enrolment.py

from .base_cleaner import standardize_columns, parse_date
from .geo_normalizer import normalize_geo

def clean_enrolment(df, pin_ref):
    df = standardize_columns(df)
    df = parse_date(df, "date")
    df.rename(columns={"date": "enrolment_date"}, inplace=True)

    # Ensure geo columns exist for fallback
    if "district" not in df.columns:
        df["district"] = None
    if "state" not in df.columns:
        df["state"] = None

    return normalize_geo(df, pin_ref)
