import os
import pandas as pd
import logging

try:
    from config import settings
    from pipelines.ingest import Ingestor
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import settings
    from pipelines.ingest import Ingestor

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Cleaner:
    """
    Handles data cleaning and standardization.
    - Date parsing
    - Missing value imputation
    - Text normalization
    """
    
    def __init__(self):
        self.date_format = settings.DATE_FORMAT
        self.output_dir = settings.PROCESSED_DATA_DIR
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

    def clean_dataset(self, df, dataset_type):
        """
        Cleans a specific dataset.
        """
        logger.info(f"Cleaning {dataset_type} dataset with {len(df)} rows.")
        
        # 1. Date Validation & Conversion
        if 'date' in df.columns:
            # Coerce errors to NaT to handle bad dates, then drop or fill if needed
            # Using specific format is much faster
            df['date'] = pd.to_datetime(df['date'], format=self.date_format, errors='coerce')
            
            # Remove rows with invalid dates if strict, or log them
            invalid_dates = df['date'].isna().sum()
            if invalid_dates > 0:
                logger.warning(f"Found {invalid_dates} rows with invalid dates in {dataset_type}. Dropping them.")
                df = df.dropna(subset=['date'])

        # 2. Text Standardization (State/District)
        for col in ['state', 'district']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.title()

        # 3. Numeric Imputation
        # Identify numeric columns for this schema
        if dataset_type == 'enrolment':
            num_cols = ['age_0_5', 'age_5_17', 'age_18_greater']
        elif dataset_type == 'demographic':
            num_cols = ['demo_age_5_17', 'demo_age_17_']
        elif dataset_type == 'biometric':
            num_cols = ['bio_age_5_17', 'bio_age_17_']
        else:
            num_cols = []
            
        for col in num_cols:
            if col in df.columns:
                # Fill NaN with 0 for counts
                df[col] = df[col].fillna(0).astype(int)

        logger.info(f"Completed cleaning {dataset_type}. Result shape: {df.shape}")
        return df

    def run(self):
        """
        Main execution method to ingest, clean, and save all datasets.
        """
        ingestor = Ingestor()
        
        for dtype in ['enrolment', 'demographic', 'biometric']:
            try:
                # 1. Ingest
                raw_df = ingestor.load_raw_data(dtype)
                
                if raw_df.empty:
                    logger.warning(f"Skipping {dtype} - No data found.")
                    continue
                    
                # 2. Clean
                clean_df = self.clean_dataset(raw_df, dtype)
                
                # 3. Save
                output_path = os.path.join(self.output_dir, f"clean_{dtype}.csv")
                # Using CSV for now for transparency, could switch to Parquet for speed
                clean_df.to_csv(output_path, index=False)
                logger.info(f"Saved cleaned data to {output_path}")
                
            except Exception as e:
                logger.error(f"Failed to process {dtype}: {e}")

if __name__ == "__main__":
    cleaner = Cleaner()
    cleaner.run()
