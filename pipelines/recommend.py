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
        self.features_dir = settings.FEATURES_DATA_DIR
        self.output_file = os.path.join(settings.DATA_DIR, "recommendations.csv")
        
    def load_forecasts(self):
        try:
            enrol = pd.read_csv(os.path.join(self.forecasts_dir, "enrolment_forecast.csv"))
            demo = pd.read_csv(os.path.join(self.forecasts_dir, "demographic_forecast.csv"))
            bio = pd.read_csv(os.path.join(self.forecasts_dir, "biometric_forecast.csv"))
            
            # Aggregate forecasts to get average demand over the horizon (Next 6 Months)
            enrol_avg = enrol.groupby(['state', 'district'])['forecast_value'].mean().reset_index().rename(columns={'forecast_value': 'avg_enrolment'})
            demo_avg = demo.groupby(['state', 'district'])['forecast_value'].mean().reset_index().rename(columns={'forecast_value': 'avg_demographic'})
            bio_avg = bio.groupby(['state', 'district'])['forecast_value'].mean().reset_index().rename(columns={'forecast_value': 'avg_biometric'})
            
            return enrol_avg, demo_avg, bio_avg
        except FileNotFoundError as e:
            logger.error(f"Cannot find forecast files: {e}")
            return None, None, None

    def load_historical_averages(self):
        """
        Calculates the average of the last 6 available months from feature files.
        Also extracts accurate latitude and longitude from PIN reference.
        """
        logger.info("Loading Historical 6-month Averages and Coordinates...")
        
        # 1. Load coordinates from authoritative reference
        coords_df = pd.DataFrame()
        ref_path = os.path.join(settings.DATA_DIR, "reference", "pin_district.csv")
        if os.path.exists(ref_path):
            ref = pd.read_csv(ref_path, low_memory=False)
            ref.columns = ref.columns.str.lower().str.strip()
            if 'latitude' in ref.columns and 'longitude' in ref.columns:
                ref['district'] = ref['district'].str.strip().str.upper()
                ref['state'] = ref['statename'].str.strip().str.upper()
                
                # Force coordinates to numeric
                ref['latitude'] = pd.to_numeric(ref['latitude'], errors='coerce')
                ref['longitude'] = pd.to_numeric(ref['longitude'], errors='coerce')
                
                # Take the mean coordinate for the district, dropping NaNs
                coords_df = ref.dropna(subset=['latitude', 'longitude']).groupby(['state', 'district'])[['latitude', 'longitude']].mean().reset_index()

        # 2. Load historical volume averages
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
                hist_avg = df.sort_values(['state', 'district', 'month']).groupby(['state', 'district']).tail(6)
                hist_avg = hist_avg.groupby(['state', 'district'])[val_col].mean().reset_index().rename(columns={val_col: new_col})
                hist_dfs.append(hist_avg)
            else:
                logger.warning(f"Feature file not found: {feat_file}")
                hist_dfs.append(None)
        
        return hist_dfs, coords_df

    def generate_recommendations(self):
        logger.info("Generating Infrastructure Recommendations (Refined Logic)...")
        
        # Load Prediction Averages
        enrol_df, demo_df, bio_df = self.load_forecasts()
        if enrol_df is None: return
        
        # Load Historical Averages & Coords
        hist_results, coords_df = self.load_historical_averages()
        hist_enrol, hist_demo, hist_bio = hist_results

        # Merge Predictions
        master = pd.merge(enrol_df, demo_df, on=['state', 'district'], how='outer')
        master = pd.merge(master, bio_df, on=['state', 'district'], how='outer')
        
        # Merge Historical Data
        if hist_enrol is not None: master = pd.merge(master, hist_enrol, on=['state', 'district'], how='left')
        if hist_demo is not None: master = pd.merge(master, hist_demo, on=['state', 'district'], how='left')
        if hist_bio is not None: master = pd.merge(master, hist_bio, on=['state', 'district'], how='left')
        
        # Merge Coordinates
        if not coords_df.empty:
            master = pd.merge(master, coords_df, on=['state', 'district'], how='left')

        master = master.fillna(0)
        
        # --- Simplified Infrastructure Logic (Prioritized Scale) ---
        def recommend_v3(row):
            enrol = row['avg_enrolment']
            demo = row['avg_demographic']
            bio = row['avg_biometric']
            total_load = enrol + demo + bio
            total_updates = demo + bio
            
            # 1. Low Activity Fallback
            if total_load < 2000:
                return "Mobile/Camp-Mode Point"

            # 2. Priority 1: High-Pressure Biometric Need
            if bio > 10000:
                return "Update-Only Center + Advanced Biometric Required"
            
            # 3. Priority 2: Volume-Based General Labels
            if total_load > 20000:
                return "Overall High Activities"
                
            if total_load > 10000:
                return "Overall Average Activities"
            
            # 4. Priority 3: Specific Focus (for 2k - 10k range)
            if enrol > (total_updates * 2):
                return "Enrolment-Centric Center"
            
            return "Update-Only Center"

        master['Recommendation'] = master.apply(recommend_v3, axis=1)
        
        # Formatting
        cols_to_round = [
            'avg_enrolment', 'avg_demographic', 'avg_biometric',
            'prev_avg_enrolment', 'prev_avg_demographic', 'prev_avg_biometric'
        ]
        for col in cols_to_round:
            if col in master.columns:
                master[col] = master[col].round(1)
        
        # Save
        master.to_csv(self.output_file, index=False)
        logger.info(f"✅ Infrastructure Recommendations saved to {self.output_file}. Rows: {len(master)}")
        
        # Summary Distribution for verification
        dist = master['Recommendation'].value_counts()
        logger.info("\nFinal Recommendation Distribution:")
        for rec_type, count in dist.items():
            logger.info(f"  - {rec_type}: {count}")

    def run(self):
        self.generate_recommendations()
        logger.info("Recommendation Engine Completed Successfully.")

if __name__ == "__main__":
    Recommender().run()
