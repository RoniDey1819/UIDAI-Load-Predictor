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

class Aggregator:
    """
    Aggregates cleaned datasets into separate monthly time-series tables.
    Strictly avoids merging datasets into a master table.
    """
    
    def __init__(self):
        self.processed_dir = settings.PROCESSED_DATA_DIR
        # Define output files strictly as per requirements
        self.enrolment_output = os.path.join(self.processed_dir, "enrolment_monthly_agg.csv")
        self.demographic_output = os.path.join(self.processed_dir, "demographic_monthly_agg.csv")
        self.biometric_output = os.path.join(self.processed_dir, "biometric_monthly_agg.csv")
        
        self.group_cols = ['state', 'district', 'month']

    def load_data(self, filename):
        """
        Loads a CSV file from the processed directory.
        """
        path = os.path.join(self.processed_dir, filename)
        if not os.path.exists(path):
            logger.warning(f"File not found: {path}")
            return pd.DataFrame()
        
        df = pd.read_csv(path)
        # Handle new date column names from clean.py
        if 'enrolment_date' in df.columns:
            df.rename(columns={'enrolment_date': 'date'}, inplace=True)
        elif 'update_date' in df.columns:
            df.rename(columns={'update_date': 'date'}, inplace=True)

        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        return df

    def aggregate_single_dataset(self, df, dataset_name):
        """
        Aggregates a single dataset by state, district, and month.
        """
        if df.empty:
            logger.warning(f"Dataset {dataset_name} is empty. Skipping aggregation.")
            return pd.DataFrame()

        # Create 'month' column (YYYY-MM-01) for grouping
        # We use the first day of the month as the representative date
        df['month'] = df['date'].dt.to_period('M').dt.to_timestamp()

        # Identify numeric columns to sum (exclude known key columns if any slipped in)
        # We know the specific columns from the schema, but dynamic is safer to catch all metric columns
        # Explicitly excluding 'pincode' from sum, as we are aggregating to district level
        exclude_cols = ['date', 'state', 'district', 'pincode', 'source_file', 'month']
        numeric_cols = [col for col in df.columns if col not in exclude_cols and pd.api.types.is_numeric_dtype(df[col])]
        
        logger.info(f"Aggregating {dataset_name} on columns: {numeric_cols}")

        # Group by state, district, month and sum
        agg_df = df.groupby(self.group_cols)[numeric_cols].sum().reset_index()
        
        # Sort for clean time-series structure
        agg_df = agg_df.sort_values(by=['state', 'district', 'month'])
        
        return agg_df

    def run(self):
        """
        Main execution method.
        """
        logger.info("Starting separate data aggregation (Step 3)...")
        
        # --- 1. Enrolment Aggregation ---
        logger.info("Processing Enrolment Data...")
        enrol_df = self.load_data("enrolment_clean.csv")
        enrol_agg = self.aggregate_single_dataset(enrol_df, "Enrolment")
        if not enrol_agg.empty:
            enrol_agg.to_csv(self.enrolment_output, index=False)
            logger.info(f"✅ Enrolment aggregation saved to {self.enrolment_output}. Rows: {len(enrol_agg)}")

        # --- 2. Demographic Aggregation ---
        logger.info("Processing Demographic Data...")
        demo_df = self.load_data("demographic_clean.csv")
        demo_agg = self.aggregate_single_dataset(demo_df, "Demographic")
        if not demo_agg.empty:
            demo_agg.to_csv(self.demographic_output, index=False)
            logger.info(f"✅ Demographic aggregation saved to {self.demographic_output}. Rows: {len(demo_agg)}")

        # --- 3. Biometric Aggregation ---
        logger.info("Processing Biometric Data...")
        bio_df = self.load_data("biometric_clean.csv")
        bio_agg = self.aggregate_single_dataset(bio_df, "Biometric")
        if not bio_agg.empty:
            bio_agg.to_csv(self.biometric_output, index=False)
            logger.info(f"✅ Biometric aggregation saved to {self.biometric_output}. Rows: {len(bio_agg)}")
            
        logger.info("Step 3 (Aggregation) Completed Successfully.")

if __name__ == "__main__":
    aggregator = Aggregator()
    aggregator.run()
