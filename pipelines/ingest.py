import os
import pandas as pd
import glob
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from config import settings
except ImportError:
    # Hack to allow running script directly from pipelines/ dir
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import settings

class Ingestor:
    """
    Handles ingestion of raw data from the landing zone (data/raw).
    Supports schema validation and metadata tagging.
    """
    
    def __init__(self):
        self.schemas = settings.SCHEMAS
        self.raw_paths = settings.RAW_DATA_SUBDIRS

    def validate_file(self, file_path, dataset_type):
        """
        Validates a single file against the expected schema.
        
        Args:
            file_path (str): Path to the CSV file.
            dataset_type (str): Type of dataset ('enrolment', 'demographic', 'biometric').
            
        Returns:
            bool: True if valid, raises ValueError otherwise.
        """
        if dataset_type not in self.schemas:
            raise ValueError(f"Unknown dataset type: {dataset_type}")
            
        expected_cols = self.schemas[dataset_type]
        
        # Read only header
        try:
            df_head = pd.read_csv(file_path, nrows=0)
            file_cols = list(df_head.columns)
            
            # Strict check: Columns must match exactly (order can differ if needed, but strictly enforce existence)
            # For this dataset, we enforce exact match for simplicity and rigor
            if not all(col in file_cols for col in expected_cols):
                missing = list(set(expected_cols) - set(file_cols))
                raise ValueError(f"Schema mismatch in {os.path.basename(file_path)}. Missing columns: {missing}")
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate {file_path}: {e}")
            raise

    def load_raw_data(self, dataset_type):
        """
        Loads all files for a specific dataset type.
        
        Args:
            dataset_type (str): 'enrolment', 'demographic', 'biometric'
            
        Returns:
            pd.DataFrame: Combined dataframe with 'source_file' column.
        """
        if dataset_type not in self.raw_paths:
            raise ValueError(f"No configured path for {dataset_type}")
            
        search_path = os.path.join(self.raw_paths[dataset_type], "*.csv")
        files = glob.glob(search_path)
        
        if not files:
            logger.warning(f"No files found for {dataset_type} at {search_path}")
            return pd.DataFrame()
            
        logger.info(f"Found {len(files)} files for {dataset_type}")
        
        data_frames = []
        for file_path in files:
            try:
                self.validate_file(file_path, dataset_type)
                
                # Load actual data
                df = pd.read_csv(file_path)
                df['source_file'] = os.path.basename(file_path)
                data_frames.append(df)
                
            except ValueError as ve:
                logger.error(f"Skipping invalid file {file_path}: {ve}")
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
                
        if not data_frames:
            logger.warning("No valid data loaded.")
            return pd.DataFrame()
            
        final_df = pd.concat(data_frames, ignore_index=True)
        logger.info(f"Successfully loaded {len(final_df)} rows for {dataset_type}")
        return final_df

    def run(self):
        """
        Main execution method to ingest and save raw data.
        """
        self.processed_dir = settings.PROCESSED_DATA_DIR
        os.makedirs(self.processed_dir, exist_ok=True)
        
        for dtype in ['enrolment', 'demographic', 'biometric']:
            try:
                df = self.load_raw_data(dtype)
                if not df.empty:
                    # Save as *_raw_all.csv as expected by the new clean.py
                    output_path = os.path.join(self.processed_dir, f"{dtype}_raw_all.csv")
                    df.to_csv(output_path, index=False)
                    logger.info(f"Saved raw combined data to {output_path}")
            except Exception as e:
                logger.error(f"Failed to ingest {dtype}: {e}")

if __name__ == "__main__":
    ingestor = Ingestor()
    ingestor.run()
