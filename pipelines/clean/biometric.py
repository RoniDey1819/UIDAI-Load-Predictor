from .base_cleaner import standardize_columns, parse_date
from .geo_normalizer import normalize_geo

def clean_biometric(df, pin_ref):
    df = standardize_columns(df)
    df = parse_date(df, "date")
    df.rename(columns={"date": "update_date"}, inplace=True)
    return normalize_geo(df, pin_ref)
