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

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Recommender:
    """
    Infrastructure Recommendation Engine.
    The ONLY place where Enrolment, Demographic, and Biometric insights are combined.
    """
    
    def __init__(self):
        self.forecasts_dir = os.path.join(settings.DATA_DIR, "forecasts")
        self.output_file = os.path.join(settings.DATA_DIR, "recommendations.csv")
        
    def load_forecasts(self):
        try:
            enrol = pd.read_csv(os.path.join(self.forecasts_dir, "enrolment_forecast.csv"))
            demo = pd.read_csv(os.path.join(self.forecasts_dir, "demographic_forecast.csv"))
            bio = pd.read_csv(os.path.join(self.forecasts_dir, "biometric_forecast.csv"))
            
            # Aggregate forecasts to get average demand over the horizon
            enrol_avg = enrol.groupby(['state', 'district'])['forecast_value'].mean().reset_index().rename(columns={'forecast_value': 'avg_enrolment'})
            demo_avg = demo.groupby(['state', 'district'])['forecast_value'].mean().reset_index().rename(columns={'forecast_value': 'avg_demographic'})
            bio_avg = bio.groupby(['state', 'district'])['forecast_value'].mean().reset_index().rename(columns={'forecast_value': 'avg_biometric'})
            
            return enrol_avg, demo_avg, bio_avg
        except FileNotFoundError as e:
            logger.error(f"Cannot find forecast files: {e}")
            return None, None, None

    def generate_recommendations(self):
        logger.info("Generating Infrastructure Recommendations...")
        
        enrol_df, demo_df, bio_df = self.load_forecasts()
        if enrol_df is None:
            return

        # Merge datasets (The only allowed join)
        master = pd.merge(enrol_df, demo_df, on=['state', 'district'], how='outer')
        master = pd.merge(master, bio_df, on=['state', 'district'], how='outer')
        
        master = master.fillna(0)
        
        # Determine Dynamic Thresholds (75th percentile)
        enrol_thresh = master['avg_enrolment'].quantile(0.75)
        demo_thresh = master['avg_demographic'].quantile(0.75)
        bio_thresh = master['avg_biometric'].quantile(0.75)
        
        logger.info(f"Thresholds -> Enrolment: {enrol_thresh:.1f}, Demographic: {demo_thresh:.1f}, Biometric: {bio_thresh:.1f}")
        
        # Logic Application
        def recommend(row):
            recs = []
            
            # Core Center Logic
            if row['avg_enrolment'] > enrol_thresh and row['avg_demographic'] > demo_thresh:
                recs.append("Full-Service ASK (High Demand)")
            elif row['avg_enrolment'] > enrol_thresh:
                recs.append("New Enrolment Center")
            elif row['avg_demographic'] > demo_thresh:
                recs.append("Update-Only Center")
            else:
                recs.append("Standard Point / Mobile Camp")
            
            # Add-ons
            if row['avg_biometric'] > bio_thresh:
                recs.append("Advanced Biometric Equipment Required")
                
            return " + ".join(recs)

        master['Recommendation'] = master.apply(recommend, axis=1)
        
        # Formatting
        master['avg_enrolment'] = master['avg_enrolment'].round(1)
        master['avg_demographic'] = master['avg_demographic'].round(1)
        master['avg_biometric'] = master['avg_biometric'].round(1)
        
        # Save
        master.to_csv(self.output_file, index=False)
        logger.info(f"✅ Infrastructure Recommendations saved to {self.output_file}. Rows: {len(master)}")
        
        # Print sample
        logger.info("Sample Recommendations:")
        logger.info(master[['state', 'district', 'Recommendation']].head(5))

    def run(self):
        self.generate_recommendations()
        logger.info("Step 6 (Recommendation Engine) Completed Successfully.")

if __name__ == "__main__":
    Recommender().run()
