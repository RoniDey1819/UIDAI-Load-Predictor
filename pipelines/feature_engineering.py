import os
import pandas as pd
import numpy as np
import logging

try:
    from config import settings
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import settings

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Generates feature datasets for each domain independently.

    Feature design philosophy:
    - No per-region seasonality assumptions
    - Emphasis on trend, volatility, and pressure indicators
    - Features are suitable for cross-region learning
    """

    def __init__(self):
        self.processed_dir = settings.PROCESSED_DATA_DIR
        self.features_dir = settings.FEATURES_DATA_DIR

        os.makedirs(self.features_dir, exist_ok=True)

        self.enrol_input = os.path.join(self.processed_dir, "enrolment_monthly_agg.csv")
        self.demo_input = os.path.join(self.processed_dir, "demographic_monthly_agg.csv")
        self.bio_input = os.path.join(self.processed_dir, "biometric_monthly_agg.csv")

        self.enrol_output = os.path.join(self.features_dir, "enrolment_features.csv")
        self.demo_output = os.path.join(self.features_dir, "demographic_features.csv")
        self.bio_output = os.path.join(self.features_dir, "biometric_features.csv")

        self.group_cols = ["state", "district"]

    # -------------------------------------------------------------------------
    def load_data(self, path):
        if not os.path.exists(path):
            logger.error(f"Input file not found: {path}")
            return pd.DataFrame()

        df = pd.read_csv(path)
        df["month"] = pd.to_datetime(df["month"])
        return df

    # -------------------------------------------------------------------------
    # Enrolment Features
    # -------------------------------------------------------------------------
    def create_enrolment_features(self):
        logger.info("Generating Enrolment Features...")
        df = self.load_data(self.enrol_input)
        if df.empty:
            return

        df = df.sort_values(self.group_cols + ["month"])

        # Core signal
        df["total_enrolment"] = (
            df["age_0_5"] + df["age_5_17"] + df["age_18_greater"]
        )

        # ---- Trend features (CRITICAL) ----
        df["lag_1"] = df.groupby(self.group_cols)["total_enrolment"].shift(1)
        df["lag_2"] = df.groupby(self.group_cols)["total_enrolment"].shift(2)

        df["growth_rate_1m"] = (df["total_enrolment"] - df["lag_1"]) / df["lag_1"]
        df["growth_rate_2m"] = (df["total_enrolment"] - df["lag_2"]) / df["lag_2"]

        # Clean infinities
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df[["growth_rate_1m", "growth_rate_2m"]] = df[
            ["growth_rate_1m", "growth_rate_2m"]
        ].fillna(0)

        # ---- Volatility (cross-region comparable) ----
        df["volatility_3m"] = (
            df.groupby(self.group_cols)["total_enrolment"]
            .transform(lambda x: x.rolling(3, min_periods=2).std())
            .fillna(0)
        )

        df.to_csv(self.enrol_output, index=False)
        logger.info(f"✅ Enrolment features saved ({len(df)} rows)")

    # -------------------------------------------------------------------------
    # Demographic Features
    # -------------------------------------------------------------------------
    def create_demographic_features(self):
        logger.info("Generating Demographic Features...")
        df = self.load_data(self.demo_input)
        if df.empty:
            return

        df = df.sort_values(self.group_cols + ["month"])

        df["total_updates"] = df["demo_age_5_17"] + df["demo_age_17_"]

        # ---- Update pressure ratio ----
        df["child_update_ratio"] = df["demo_age_5_17"] / df["total_updates"]
        df["child_update_ratio"] = df["child_update_ratio"].fillna(0)

        # ---- Trend & volatility ----
        df["lag_1"] = df.groupby(self.group_cols)["total_updates"].shift(1)
        df["growth_rate_1m"] = (df["total_updates"] - df["lag_1"]) / df["lag_1"]
        df["growth_rate_1m"] = df["growth_rate_1m"].replace(
            [np.inf, -np.inf], np.nan
        ).fillna(0)

        df["volatility_3m"] = (
            df.groupby(self.group_cols)["total_updates"]
            .transform(lambda x: x.rolling(3, min_periods=2).std())
            .fillna(0)
        )

        df.to_csv(self.demo_output, index=False)
        logger.info(f"✅ Demographic features saved ({len(df)} rows)")

    # -------------------------------------------------------------------------
    # Biometric Features
    # -------------------------------------------------------------------------
    def create_biometric_features(self):
        logger.info("Generating Biometric Features...")
        df = self.load_data(self.bio_input)
        if df.empty:
            return

        df = df.sort_values(self.group_cols + ["month"])

        df["total_biometric"] = df["bio_age_5_17"] + df["bio_age_17_"]

        # ---- Mandatory biometric ageing pressure ----
        df["mandatory_update_pressure"] = (
            df["bio_age_5_17"] / df["total_biometric"]
        ).fillna(0)

        # ---- Trend & volatility ----
        df["lag_1"] = df.groupby(self.group_cols)["total_biometric"].shift(1)
        df["growth_rate_1m"] = (df["total_biometric"] - df["lag_1"]) / df["lag_1"]
        df["growth_rate_1m"] = df["growth_rate_1m"].replace(
            [np.inf, -np.inf], np.nan
        ).fillna(0)

        df["volatility_3m"] = (
            df.groupby(self.group_cols)["total_biometric"]
            .transform(lambda x: x.rolling(3, min_periods=2).std())
            .fillna(0)
        )

        df.to_csv(self.bio_output, index=False)
        logger.info(f"✅ Biometric features saved ({len(df)} rows)")

    # -------------------------------------------------------------------------
    def run(self):
        self.create_enrolment_features()
        self.create_demographic_features()
        self.create_biometric_features()
        logger.info("Step 4 (Feature Engineering) completed successfully.")


if __name__ == "__main__":
    FeatureEngineer().run()
