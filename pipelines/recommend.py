import os
import pandas as pd
import logging
import numpy as np

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


class Recommender:
    """
    Infrastructure Recommendation Engine.

    Philosophy:
    - Rank regions RELATIVELY using a composite demand score
    - Convert scores into percentile-based infrastructure categories
    - Add biometric capability flags independently of center type
    """

    def __init__(self):
        self.forecasts_dir = os.path.join(settings.DATA_DIR, "forecasts")
        self.features_dir = settings.FEATURES_DATA_DIR
        self.output_file = os.path.join(settings.DATA_DIR, "recommendations.csv")

    # -------------------------------------------------------------------------
    def load_forecasts(self):
        try:
            enrol = pd.read_csv(os.path.join(self.forecasts_dir, "enrolment_forecast.csv"))
            demo = pd.read_csv(os.path.join(self.forecasts_dir, "demographic_forecast.csv"))
            bio = pd.read_csv(os.path.join(self.forecasts_dir, "biometric_forecast.csv"))

            enrol_avg = enrol.groupby(['state', 'district'])['forecast_value'].mean() \
                             .reset_index().rename(columns={'forecast_value': 'avg_enrolment'})

            demo_avg = demo.groupby(['state', 'district'])['forecast_value'].mean() \
                           .reset_index().rename(columns={'forecast_value': 'avg_demographic'})

            bio_avg = bio.groupby(['state', 'district'])['forecast_value'].mean() \
                          .reset_index().rename(columns={'forecast_value': 'avg_biometric'})

            return enrol_avg, demo_avg, bio_avg

        except FileNotFoundError as e:
            logger.error(f"Forecast files missing: {e}")
            return None, None, None

    # -------------------------------------------------------------------------
    def load_historical_averages(self):
        logger.info("Loading historical 6-month averages...")

        tasks = [
            ('enrolment_features.csv', 'total_enrolment', 'prev_avg_enrolment'),
            ('demographic_features.csv', 'total_updates', 'prev_avg_demographic'),
            ('biometric_features.csv', 'total_biometric', 'prev_avg_biometric')
        ]

        results = []
        for feat_file, val_col, out_col in tasks:
            path = os.path.join(self.features_dir, feat_file)
            if os.path.exists(path):
                df = pd.read_csv(path)
                df['month'] = pd.to_datetime(df['month'])
                avg_df = (
                    df.sort_values(['state', 'district', 'month'])
                      .groupby(['state', 'district'])
                      .tail(6)
                      .groupby(['state', 'district'])[val_col]
                      .mean()
                      .reset_index()
                      .rename(columns={val_col: out_col})
                )
                results.append(avg_df)
            else:
                results.append(None)

        return results

    # -------------------------------------------------------------------------
    def generate_recommendations(self):
        logger.info("Generating Infrastructure Recommendations (Final Logic)...")

        enrol_df, demo_df, bio_df = self.load_forecasts()
        if enrol_df is None:
            return

        hist_enrol, hist_demo, hist_bio = self.load_historical_averages()

        master = enrol_df.merge(demo_df, on=['state', 'district'], how='outer') \
                          .merge(bio_df, on=['state', 'district'], how='outer')

        if hist_enrol is not None:
            master = master.merge(hist_enrol, on=['state', 'district'], how='left')
        if hist_demo is not None:
            master = master.merge(hist_demo, on=['state', 'district'], how='left')
        if hist_bio is not None:
            master = master.merge(hist_bio, on=['state', 'district'], how='left')

        master = master.fillna(0)

        # ---------------------------------------------------------------------
        # 1️⃣ SCORE COMPUTATION
        # ---------------------------------------------------------------------

        # Growth signal (forecast vs recent history)
        master['growth_score'] = (
            (master['avg_enrolment'] - master['prev_avg_enrolment']) /
            master['prev_avg_enrolment'].replace(0, np.nan)
        ).replace([np.inf, -np.inf], 0).fillna(0)

        # Update pressure signal
        total_updates = master['avg_demographic'] + master['avg_biometric']
        master['update_pressure_score'] = total_updates / (master['avg_enrolment'] + 1)

        # Biometric stress signal
        master['biometric_stress_score'] = master['avg_biometric'] / (total_updates + 1)

        # Normalize all scores (relative ranking)
        for col in ['growth_score', 'update_pressure_score', 'biometric_stress_score']:
            max_val = master[col].abs().max()
            if max_val > 0:
                master[col] = master[col] / max_val

        # Composite Infrastructure Demand Score
        master['infra_demand_score'] = (
            0.4 * master['growth_score'] +
            0.3 * master['update_pressure_score'] +
            0.3 * master['biometric_stress_score']
        )

        # ---------------------------------------------------------------------
        # 2️⃣ PERCENTILE-BASED CATEGORY MAPPING (CRITICAL FIX)
        # ---------------------------------------------------------------------
        p20 = master['infra_demand_score'].quantile(0.20)
        p40 = master['infra_demand_score'].quantile(0.40)
        p60 = master['infra_demand_score'].quantile(0.60)
        p80 = master['infra_demand_score'].quantile(0.80)

        def map_recommendation(score):
            if score < p20:
                return "Mobile/Camp-Mode Point"
            if score < p40:
                return "Update-Only Center"
            if score < p60:
                return "Enrolment-Centric Center"
            if score < p80:
                return "Overall Average Activities"
            return "Overall High Activities"

        master['Recommendation'] = master['infra_demand_score'].apply(map_recommendation)

        # ---------------------------------------------------------------------
        # 3️⃣ BIOMETRIC CAPABILITY OVERRIDE (ADDITIVE, NOT REPLACEMENT)
        # ---------------------------------------------------------------------
        def add_biometric_flag(row):
            if row['prev_avg_biometric'] >= 10000:
                return row['Recommendation'] + " + Advanced Biometric Infrastructure Needed"
            return row['Recommendation']

        master['Recommendation'] = master.apply(add_biometric_flag, axis=1)

        # ---------------------------------------------------------------------
        # OUTPUT
        # ---------------------------------------------------------------------
        master.to_csv(self.output_file, index=False)
        logger.info(f"✅ Final Recommendations saved ({len(master)} rows)")

        logger.info("\nFinal Recommendation Distribution:")
        for k, v in master['Recommendation'].value_counts().items():
            logger.info(f"  - {k}: {v}")

    # -------------------------------------------------------------------------
    def run(self):
        self.generate_recommendations()
        logger.info("Recommendation Engine Completed Successfully.")


if __name__ == "__main__":
    Recommender().run()
