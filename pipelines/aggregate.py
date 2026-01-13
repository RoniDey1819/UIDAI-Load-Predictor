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
    Aggregates cleaned datasets into district-level separate monthly time-series tables.
    Aggregation is performed by summing pre-aggregated numeric metric columns (eg: age-wise counts)
    Aggregation level: state + district + month
    Pincode-level granularity intentionally dropped
    """
    
    # Explicit metric columns per dataset
    METRIC_COLUMNS = {
        "Enrolment" : ["age_0_5", "age_5_17", "age_18_greater"],
        "Demographic": ["demo_age_5_17", "demo_age_17_"],
        "Biometric": ["bio_age_5_17", "bio_age_17_"],
    }

    def __init__(self):
        self.processed_dir = settings.PROCESSED_DATA_DIR
        # Output files
        self.enrolment_output = os.path.join(self.processed_dir, "enrolment_monthly_agg.csv")
        self.demographic_output = os.path.join(self.processed_dir, "demographic_monthly_agg.csv")
        self.biometric_output = os.path.join(self.processed_dir, "biometric_monthly_agg.csv")
        
        # Aggregating keys (district-level by design)
        self.group_cols = ['state', 'district', 'month']

    def load_data(self, filename):
        """
        Loads a CSV file from the processed directory and noralizes date column
        """
        path = os.path.join(self.processed_dir, filename)
        if not os.path.exists(path):
            logger.warning(f"File not found: {path}")
            return pd.DataFrame()
        
        df = pd.read_csv(path)

        # Normalize date column name
        if 'enrolment_date' in df.columns:
            df.rename(columns={'enrolment_date': 'date'}, inplace=True)
        elif 'update_date' in df.columns:
            df.rename(columns={'update_date': 'date'}, inplace=True)

        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors="coerce")

        if 'date' not in df.columns:
            logger.error("No date column found after renaming.")
            return pd.DataFrame()
        return df

    def aggregate_single_dataset(self, df, dataset_name):
        """
        Aggregates a single dataset by state, district, and month.
        """
        if df.empty:
            logger.warning(f"Dataset {dataset_name} is empty. Skipping aggregation.")
            return pd.DataFrame()
        
        #Drop invalid geography
        df = df.dropna(subset=["state", "district", "date"])
        df = df[~df["state"].str.upper().eq("UNKNOWN")]
        df = df[~df["district"].str.upper().eq("UNKNOWN")]

        #Ensure valid dates
        df['date'] = pd.to_datetime(df['date'], errors="coerce")
        df = df.dropna(subset=["date"])

        # Create 'month' column (YYYY-MM-01) for grouping
        # We use the first day of the month as the representative date
        df['month'] = df['date'].dt.to_period('M').dt.to_timestamp()

        # Explicitly define metric columns based on dataset schema.
        # Dynamic numeric detection is intentionally avoided to prevent
        # accidental aggregation of non-metric numeric fields (e.g., pincode).
        metric_cols = self.METRIC_COLUMNS.get(dataset_name)
        if not metric_cols:
            logger.error(f"No metric columns defined for {dataset_name}")
            return pd.DataFrame()
        
        missing_metrics = [c for c in metric_cols if c not in df.columns]
        if missing_metrics:
            logger.error(
                f"Missing metric columns in {dataset_name}: {missing_metrics}"
            )
        
        logger.info(f"Aggregating {dataset_name} on columns: {metric_cols}")

        # Aggregation
        agg_df = (
            df.groupby(self.group_cols)[metric_cols]
            .sum()
            .reset_index()
            .sort_values(by=self.group_cols)
        )
        
        # Total column (useful for forecasting and dashboards)
        agg_df["total"] = agg_df[metric_cols].sum(axis=1)
        
        return agg_df
    
    # -------------------------------------------------------------------------
    # Validation helpers
    # -------------------------------------------------------------------------
    @staticmethod
    def validate_sum_conservation(
        clean_df: pd.DataFrame,
        agg_df: pd.DataFrame,
        metric_cols: list,
        dataset_name: str,
    ) -> None:
        """
        Ensures that the sum of metrics in the aggregated data
        matches the sum in the cleaned data.
        """
        filtered_clean = clean_df.dropna(subset=["state", "district", "date"])
        filtered_clean = filtered_clean[~filtered_clean["state"].str.upper().eq("UNKNOWN")]
        filtered_clean = filtered_clean[~filtered_clean["district"].str.upper().eq("UNKNOWN")]

        clean_sum = filtered_clean[metric_cols].sum().sum()

        agg_sum = agg_df[metric_cols].sum().sum()

        if abs(clean_sum - agg_sum) > 1e-6:
            raise ValueError(
                f"{dataset_name} aggregation failed sum check: "
                f"clean={clean_sum}, agg={agg_sum}"
            )

        logger.info(
            f"{dataset_name} sum validation passed "
            f"(total={clean_sum})"
        )

    # -------------------------------------------------------------------------
    # Main execution
    # -------------------------------------------------------------------------
    def run(self):
        logger.info("Starting data aggregation (Step 3)...")

        # ---------------- Enrolment ----------------
        logger.info("Processing Enrolment data...")
        enrol_df = self.load_data("enrolment_clean.csv")
        enrol_agg = self.aggregate_single_dataset(enrol_df, "Enrolment")

        if not enrol_agg.empty:
            self.validate_sum_conservation(
                enrol_df,
                enrol_agg,
                self.METRIC_COLUMNS["Enrolment"],
                "Enrolment",
            )
            enrol_agg.to_csv(self.enrolment_output, index=False)
            logger.info(
                f"✅ Enrolment aggregation saved "
                f"({len(enrol_agg)} rows)"
            )

        # ---------------- Demographic ----------------
        logger.info("Processing Demographic data...")
        demo_df = self.load_data("demographic_clean.csv")
        demo_agg = self.aggregate_single_dataset(demo_df, "Demographic")

        if not demo_agg.empty:
            self.validate_sum_conservation(
                demo_df,
                demo_agg,
                self.METRIC_COLUMNS["Demographic"],
                "Demographic",
            )
            demo_agg.to_csv(self.demographic_output, index=False)
            logger.info(
                f"✅ Demographic aggregation saved "
                f"({len(demo_agg)} rows)"
            )

        # ---------------- Biometric ----------------
        logger.info("Processing Biometric data...")
        bio_df = self.load_data("biometric_clean.csv")
        bio_agg = self.aggregate_single_dataset(bio_df, "Biometric")

        if not bio_agg.empty:
            self.validate_sum_conservation(
                bio_df,
                bio_agg,
                self.METRIC_COLUMNS["Biometric"],
                "Biometric",
            )
            bio_agg.to_csv(self.biometric_output, index=False)
            logger.info(
                f"✅ Biometric aggregation saved "
                f"({len(bio_agg)} rows)"
            )

        logger.info("Step 3 (Aggregation) completed successfully.")


if __name__ == "__main__":
    Aggregator().run()
