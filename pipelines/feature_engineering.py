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

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FeatureEngineer:
    """
    Generates feature datasets for each domain independently.
    Strictly avoids cross-domain joins.
    """
    
    def __init__(self):
        self.processed_dir = settings.PROCESSED_DATA_DIR
        self.features_dir = settings.FEATURES_DATA_DIR
        
        # Ensure feature directory exists
        os.makedirs(self.features_dir, exist_ok=True)
        
        # Define I/O paths
        self.enrol_input = os.path.join(self.processed_dir, "enrolment_monthly_agg.csv")
        self.demo_input = os.path.join(self.processed_dir, "demographic_monthly_agg.csv")
        self.bio_input = os.path.join(self.processed_dir, "biometric_monthly_agg.csv")
        
        self.enrol_output = os.path.join(self.features_dir, "enrolment_features.csv")
        self.demo_output = os.path.join(self.features_dir, "demographic_features.csv")
        self.bio_output = os.path.join(self.features_dir, "biometric_features.csv")
        
        self.group_cols = ['state', 'district']

    def load_data(self, path):
        if not os.path.exists(path):
            logger.error(f"Input file not found: {path}")
            return pd.DataFrame()
        df = pd.read_csv(path)
        if 'month' in df.columns:
            df['month'] = pd.to_datetime(df['month'])
        return df

    def create_enrolment_features(self):
        logger.info("Generating Enrolment Features...")
        df = self.load_data(self.enrol_input)
        if df.empty: return

        # 1. Total Enrolment Count
        df['total_enrolment'] = df['age_0_5'] + df['age_5_17'] + df['age_18_greater']
        
        # 2. Seasonality Indicators (Month of year)
        df['month_num'] = df['month'].dt.month
        df['is_quarter_end'] = df['month'].dt.is_quarter_end.astype(int)

        # 3. Growth Rate (Month-over-Month)
        # Sort by group cols and time
        df = df.sort_values(by=self.group_cols + ['month'])
        
        # Calculate lag
        df['prev_month_enrolment'] = df.groupby(self.group_cols)['total_enrolment'].shift(1)
        
        # Growth Rate = (Current - Prev) / Prev
        # Handle division by zero or NaN
        df['growth_rate'] = (df['total_enrolment'] - df['prev_month_enrolment']) / df['prev_month_enrolment']
        df['growth_rate'] = df['growth_rate'].fillna(0) # First month 0 growth
        
        # Clean up intermediate columns? Keeping them might be useful for model
        
        features = df
        
        # Save
        features.to_csv(self.enrol_output, index=False)
        logger.info(f"✅ Enrolment features saved to {self.enrol_output}. Rows: {len(features)}")

    def create_demographic_features(self):
        logger.info("Generating Demographic Features...")
        df = self.load_data(self.demo_input)
        if df.empty: return
        
        # 1. Total Updates
        df['total_updates'] = df['demo_age_5_17'] + df['demo_age_17_']
        
        # 2. Update-Type Distribution
        # Ratio of younger age group updates
        df['child_update_ratio'] = df['demo_age_5_17'] / df['total_updates']
        df['child_update_ratio'] = df['child_update_ratio'].fillna(0)

        # 3. Spike Indicators
        # Compare current with 3-month rolling mean
        df = df.sort_values(by=self.group_cols + ['month'])
        
        df['rolling_mean_3m'] = df.groupby(self.group_cols)['total_updates'].transform(lambda x: x.rolling(window=3, min_periods=1).mean())
        df['rolling_std_3m'] = df.groupby(self.group_cols)['total_updates'].transform(lambda x: x.rolling(window=3, min_periods=1).std())
        df['rolling_std_3m'] = df['rolling_std_3m'].fillna(0)
        
        # Simple spike: if value > mean + 1.5 * std (and std > 0)
        # Avoiding division by zero issues
        threshold = df['rolling_mean_3m'] + 1.5 * df['rolling_std_3m']
        df['is_spike'] = (df['total_updates'] > threshold).astype(int)
        
        features = df
        features.to_csv(self.demo_output, index=False)
        logger.info(f"✅ Demographic features saved to {self.demo_output}. Rows: {len(features)}")

    def create_biometric_features(self):
        logger.info("Generating Biometric Features...")
        df = self.load_data(self.bio_input)
        if df.empty: return
        
        # 1. Total Biometric Updates
        df['total_biometric'] = df['bio_age_5_17'] + df['bio_age_17_']
        
        # 2. Modality-wise pressure (Using the raw counts as features is good)
        # We already have bio_age_5_17 and bio_age_17_ which are proxies for modality/age groups.
        
        # 3. Age-linked stress
        # Ratio of 5-17 vs 17+ (Mandatory biometric updates usually happen at 5 and 15)
        # High ratio of 5-17 suggests mandatory update pressure
        df['mandatory_update_pressure'] = df['bio_age_5_17'] / df['total_biometric']
        df['mandatory_update_pressure'] = df['mandatory_update_pressure'].fillna(0)
        
        # Seasonality
        df['month_num'] = df['month'].dt.month
        
        features = df
        features.to_csv(self.bio_output, index=False)
        logger.info(f"✅ Biometric features saved to {self.bio_output}. Rows: {len(features)}")

    def run(self):
        self.create_enrolment_features()
        self.create_demographic_features()
        self.create_biometric_features()
        logger.info("Step 4 (Feature Engineering) Completed Successfully.")

if __name__ == "__main__":
    fe = FeatureEngineer()
    fe.run()
