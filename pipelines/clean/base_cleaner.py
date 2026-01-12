# pipelines/clean/base_cleaner.py

import pandas as pd

def standardize_columns(df):
    df.columns = df.columns.str.lower().str.strip()
    return df


def parse_date(df, col_name):
    df[col_name] = pd.to_datetime(
    df[col_name],
    dayfirst=True,
    errors="coerce"
    )

    return df

