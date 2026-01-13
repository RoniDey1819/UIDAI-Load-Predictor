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

    Design philosophy:
    - Use relative growth & pressure signals, not absolute forecasts
    - Convert signals into a single Infrastructure Demand Score
    - Map score to actionable infrastructure labels
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
            logger.error(f"Cannot find forecast files: {e}")
            return None, None, None

    # -------------------------------------------------------------------------
    def load_historical_averages(self):
        logger.info("Loading Historical Averages...")

        tasks = [
            ('enrolment_features.csv', 'total_enrolment', 'prev_avg_enrolment'),
            ('demographic_features.csv', 'total_updates', 'prev_avg_demographic'),
            ('biometric_features.csv', 'total_biometric', 'prev_avg_biometric')
        ]

        hist_dfs = []
        for feat_file, val_col, new_col in tasks:
            path = os.path.join(self.features_dir, feat_file)
            if os.path.exists(path):
                df = pd.read_csv(path)
                df['month'] = pd.to_datetime(df['month'])
                last_vals = (
                    df.sort_values(['state', 'district', 'month'])
                      .groupby(['state', 'district'])
                      .tail(6)
                      .groupby(['state', 'district'])[val_col]
                      .mean()
                      .reset_index()
                      .rename(columns={val_col: new_col})
                )
                hist_dfs.append(last_vals)
            else:
                hist_dfs.append(None)

        return hist_dfs

    # -------------------------------------------------------------------------
    def generate_recommendations(self):
        logger.info("Generating Infrastructure Recommendations (Score-Based)...")

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
        # Score Computation (CORE CHANGE)
        # ---------------------------------------------------------------------

        # 1. Growth score (forecast vs historical)
        master['growth_score'] = (
            (master['avg_enrolment'] - master['prev_avg_enrolment']) /
            master['prev_avg_enrolment'].replace(0, np.nan)
        ).replace([np.inf, -np.inf], 0).fillna(0)

        # 2. Update pressure score
        total_updates = master['avg_demographic'] + master['avg_biometric']
        master['update_pressure_score'] = (
            total_updates / (master['avg_enrolment'] + 1)
        )

        # 3. Biometric stress score
        master['biometric_stress_score'] = (
            master['avg_biometric'] / (total_updates + 1)
        )

        # Normalize scores (0–1 range)
        for col in ['growth_score', 'update_pressure_score', 'biometric_stress_score']:
            max_val = master[col].abs().max()
            if max_val > 0:
                master[col] = master[col] / max_val

        # Infrastructure Demand Score (weighted)
        master['infra_demand_score'] = (
            0.4 * master['growth_score'] +
            0.3 * master['update_pressure_score'] +
            0.3 * master['biometric_stress_score']
        )

        # ---------------------------------------------------------------------
        # Score → Recommendation Mapping
        # ---------------------------------------------------------------------
        def map_recommendation(row):
            score = row['infra_demand_score']

            if score < 0.2:
                return "Mobile/Camp-Mode Point"
            if score < 0.4:
                return "Update-Only Center"
            if score < 0.6:
                return "Enrolment-Centric Center"
            if score < 0.8:
                return "Overall Average Activities"

            return "Overall High Activities + Advanced Biometric"

        master['Recommendation'] = master.apply(map_recommendation, axis=1)

        master.to_csv(self.output_file, index=False)
        logger.info(
            f"✅ Infrastructure Recommendations saved ({len(master)} rows)"
        )

        logger.info("\nFinal Recommendation Distribution:")
        for k, v in master['Recommendation'].value_counts().items():
            logger.info(f"  - {k}: {v}")

    # -------------------------------------------------------------------------
    def run(self):
        self.generate_recommendations()
        logger.info("Recommendation Engine Completed Successfully.")


if __name__ == "__main__":
    Recommender().run()
