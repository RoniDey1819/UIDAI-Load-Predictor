import os
import pandas as pd
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

class Validator:
    """
    Validates data integrity and schema across all stages.
    """
    def __init__(self):
        self.processed_dir = settings.PROCESSED_DATA_DIR
        self.features_dir = settings.FEATURES_DATA_DIR
        self.forecast_dir = os.path.join(settings.DATA_DIR, "forecasts")

    def check_file(self, path, expected_cols=None):
        if not os.path.exists(path):
            logger.error(f"Missing File: {path}")
            return False
        
        try:
            df = pd.read_csv(path)
            if df.empty:
                logger.error(f"Empty File: {path}")
                return False
            
            if expected_cols:
                missing = [col for col in expected_cols if col not in df.columns]
                if missing:
                    logger.error(f"Schema Mismatch in {path}: Missing {missing}")
                    return False
            
            logger.info(f"Valid: {os.path.basename(path)} ({len(df)} rows)")
            return True
        except Exception as e:
            logger.error(f"Error reading {path}: {str(e)}")
            return False

    def validate_all(self):
        logger.info("Starting Data Validation...")
        
        # 1. Processed Data
        processed_files = [
            ("enrolment_monthly_agg.csv", ['state', 'district', 'month']),
            ("demographic_monthly_agg.csv", ['state', 'district', 'month']),
            ("biometric_monthly_agg.csv", ['state', 'district', 'month'])
        ]
        
        for file, cols in processed_files:
            self.check_file(os.path.join(self.processed_dir, file), cols)

        # 2. Features
        feature_files = [
            ("enrolment_features.csv", ['total_enrolment']),
            ("demographic_features.csv", ['total_updates']),
            ("biometric_features.csv", ['total_biometric'])
        ]
        
        for file, cols in feature_files:
            self.check_file(os.path.join(self.features_dir, file), cols)

        # 3. Forecasts
        forecast_files = [
            ("enrolment_forecast.csv", ['forecast_value']),
            ("demographic_forecast.csv", ['forecast_value']),
            ("biometric_forecast.csv", ['forecast_value'])
        ]
        
        for file, cols in forecast_files:
            self.check_file(os.path.join(self.forecast_dir, file), cols)

        # 4. Final Recommendations
        self.check_file(os.path.join(settings.DATA_DIR, "recommendations.csv"), ['Recommendation'])

        logger.info("Validation Complete.")

if __name__ == "__main__":
    Validator().validate_all()
