# pipelines/clean/enrolment.py

from .base_cleaner import standardize_columns, parse_date
from .geo_normalizer import normalize_geo

def clean_enrolment(df, pin_ref):
    df = standardize_columns(df)
    df = parse_date(df, "date")
    df.rename(columns={"date": "enrolment_date"}, inplace=True)
    return normalize_geo(df, pin_ref)
