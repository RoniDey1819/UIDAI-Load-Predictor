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
    - Absolute Demand Tiers: Recommendations based on capacity needs, not just ranking.
    - Volume Weighting: High-volume hubs are prioritized over low-volume ratios.
    - Logistical Load: Composite score integrates growth, update pressure, and biometric stress.
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
        logger.info("Loading recent historical averages...")

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
                
                # Use mean of up to last 6 months (robust for shallow data)
                avg_df = (
                    df.sort_values(['state', 'district', 'month'])
                      .groupby(['state', 'district'])[val_col]
                      .apply(lambda x: x.tail(6).mean()) # Handle <6 points naturally
                      .reset_index()
                      .rename(columns={val_col: out_col})
                )
                results.append(avg_df)
            else:
                results.append(None)

        return results

    # -------------------------------------------------------------------------
    def generate_recommendations(self):
        logger.info("Generating Infrastructure Recommendations (Absolute Tiers)...")

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
        # 1️⃣ LOAD & GROWTH COMPUTATION
        # ---------------------------------------------------------------------
        total_monthly_demand = master['avg_enrolment'] + master['avg_demographic'] + master['avg_biometric']
        prev_total_demand = master['prev_avg_enrolment'] + master['prev_avg_demographic'] + master['prev_avg_biometric']
        
        # Absolute volume weight (Logarithmic to handle Metros vs Villages)
        master['volume_weight'] = np.log10(total_monthly_demand + 1)

        # Growth signal (forecast vs recent history)
        master['growth_rate'] = (
            (total_monthly_demand - prev_total_demand) /
            prev_total_demand.replace(0, np.nan)
        ).replace([np.inf, -np.inf], 0).fillna(0)

        # ---------------------------------------------------------------------
        # 2️⃣ COMPOSITE DEMAND SCORE (VOLUME WEIGHTED)
        # ---------------------------------------------------------------------
        # Pressure Ratios
        update_pressure = (master['avg_demographic'] + master['avg_biometric']) / (master['avg_enrolment'] + 1)
        biometric_stress = master['avg_biometric'] / (master['avg_demographic'] + master['avg_biometric'] + 1)

        # Demand Score = [Growth + Update Pressure + Biometric Stress] * VolumeWeight
        # This ensures high-volume areas with high stress rank highest.
        master['infra_demand_score'] = (
            (0.4 * master['growth_rate']) + 
            (0.3 * update_pressure.clip(0, 5)) + 
            (0.3 * biometric_stress)
        ) * master['volume_weight']

        # ---------------------------------------------------------------------
        # 3️⃣ BEHAVIORAL & CAPACITY CATEGORIZATION
        # ---------------------------------------------------------------------
        def map_recommendation(row):
            load = row['avg_enrolment'] + row['avg_demographic'] + row['avg_biometric']
            enrolment = row['avg_enrolment']
            growth = row['growth_rate']
            
            # --- Tier 1: Emergency / Extreme Demand (>50k or Huge Surge) ---
            if load > 50000 or (load > 15000 and growth > 0.6):
                return "Overall High Activities"
            
            # --- Tier 2: High-Volume Hub (>20k) ---
            if load > 20000:
                return "Overall Average Activities"
            
            # --- Tier 3/4: Medium-Volume Behavioral Split ---
            # If enrolment volume is significant, mark as Enrolment-Centric
            if load > 2000:
                if enrolment > 2000:
                    return "Enrolment-Centric Center"
                else:
                    return "Update-Only Center"
            
            # --- Tier 5: Low Demand / Sparse ---
            return "Mobile/Camp-Mode Point"

        master['Recommendation'] = master.apply(map_recommendation, axis=1)

        # ---------------------------------------------------------------------
        # 4️⃣ BIOMETRIC INFRASTRUCTURE OVERRIDE
        # ---------------------------------------------------------------------
        def add_biometric_flag(row):
            # If biometric load is SIGNIFICANT (>15,000 monthly), flag for advanced machines
            if row['avg_biometric'] > 15000:
                return row['Recommendation'] + " + Advanced Biometric Infrastructure Recommended"
            return row['Recommendation']

        master['Recommendation'] = master.apply(add_biometric_flag, axis=1)

        # ---------------------------------------------------------------------
        # OUTPUT
        # ---------------------------------------------------------------------
        master.to_csv(self.output_file, index=False)
        logger.info(f"✅ Enhanced Recommendations saved ({len(master)} rows)")

        logger.info("\nFinal Recommendation Distribution (Absolute Tiers):")
        for k, v in master['Recommendation'].value_counts().items():
            logger.info(f"  - {k}: {v}")

    # -------------------------------------------------------------------------
    def run(self):
        self.generate_recommendations()
        logger.info("Recommendation Engine Completed Successfully.")


if __name__ == "__main__":
    Recommender().run()
