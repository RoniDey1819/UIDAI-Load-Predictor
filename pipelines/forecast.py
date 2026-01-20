import os
import pandas as pd
import numpy as np
import logging
import multiprocessing as mp
from functools import partial
import warnings

try:
    from config import settings
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import settings

warnings.filterwarnings("ignore")

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Helper: trend-based forecasting for one district
# -----------------------------------------------------------------------------
def predict_next_month(y_history, global_growth, growth_bounds):
    """
    Predicts the next single value using a sliding window and hierarchical shrinkage.
    """
    n = len(y_history)
    
    # Use a sliding window of recent data (e.g., last 6-12 months)
    # If we have enough data, focus on the last 12 points to capture recent shifts
    window_size = 12
    y_window = y_history[-window_size:]
    nw = len(y_window)

    # -----------------------------
    # Step 1: Local trend estimation
    # -----------------------------
    if nw >= 3:
        x = np.arange(nw)
        slope, _ = np.polyfit(x, y_window, 1)
        # Avoid division by zero
        local_growth = slope / max(y_window.mean(), 1)
    else:
        local_growth = 0.0

    # -----------------------------
    # Step 2: Hierarchical shrinkage
    # -----------------------------
    # Confidence in local trend grows with total history (n)
    alpha = min(1.0, max(0.0, (n - 1) / 6))
    growth_rate = alpha * local_growth + (1 - alpha) * global_growth

    # -----------------------------
    # Step 3: Data-driven safety bounds
    # -----------------------------
    lower, upper = growth_bounds
    growth_rate = np.clip(growth_rate, lower, upper)

    # -----------------------------
    # Step 4: Step-ahead prediction
    # -----------------------------
    last_val = y_history[-1]
    prediction = last_val * (1 + growth_rate)
    return max(0, prediction)


def fit_single_district(group_data, horizon, value_col, global_growth, growth_bounds):
    """
    Recursive sliding window forecasting for a single district.
    """
    (state, district), group = group_data

    try:
        group = group.sort_values("month")
        y_history = list(group[value_col].values)
        
        preds = []
        
        # Recursive Step-by-Step Prediction
        for _ in range(horizon):
            next_val = predict_next_month(np.array(y_history), global_growth, growth_bounds)
            preds.append(next_val)
            # Add prediction back to history for the next iteration (Sliding Window)
            y_history.append(next_val)

        # -----------------------------
        # Output formatting
        # -----------------------------
        last_date = group["month"].iloc[-1]
        future_dates = pd.date_range(
            start=last_date, periods=horizon + 1, freq="MS"
        )[1:]

        return [
            {
                "state": state,
                "district": district,
                "month": date.date(),
                "forecast_value": int(round(val)),
            }
            for date, val in zip(future_dates, preds)
        ]

    except Exception as e:
        logger.error(f"Error forecasting district {district} in {state}: {str(e)}")
        return []


# -----------------------------------------------------------------------------
# Forecaster
# -----------------------------------------------------------------------------
class Forecaster:
    """
    Trend-based forecasting engine with hierarchical (cross-region) borrowing.

    Key principles:
    - No seasonality assumptions
    - Linear trend estimation (robust for short series)
    - Global-to-local shrinkage for statistical stability
    """

    def __init__(self):
        self.features_dir = settings.FEATURES_DATA_DIR
        self.forecasts_dir = os.path.join(settings.DATA_DIR, "forecasts")
        os.makedirs(self.forecasts_dir, exist_ok=True)
        self.horizon = 6

    def forecast_series(self, df, value_col, name, output_file):
        logger.info(f"Forecasting {name} using hierarchical trend extrapolation...")

        # -----------------------------
        # Step A: Compute GLOBAL (time-aware) growth
        # -----------------------------
        # Aggregate all regions by month → a true national/global series
        global_series = (
            df.groupby("month")[value_col]
              .sum()
              .sort_index()
        )

        if len(global_series) >= 3:
            x = np.arange(len(global_series))
            global_slope, _ = np.polyfit(x, global_series.values, 1)
            global_growth = global_slope / max(global_series.mean(), 1)
        else:
            global_growth = 0.0

        # -----------------------------
        # Step B: Data-driven growth bounds
        # -----------------------------
        # Bounds derived from global volatility (not magic numbers)
        diffs = np.diff(global_series.values) if len(global_series) > 1 else np.array([0])
        sigma = np.std(diffs) / max(global_series.mean(), 1)

        # Conservative but explainable bounds
        lower_bound = -2 * sigma
        upper_bound =  2 * sigma

        # Final safety clamp (domain realism)
        lower_bound = max(lower_bound, -0.20)
        upper_bound = min(upper_bound,  0.30)

        growth_bounds = (lower_bound, upper_bound)

        # -----------------------------
        # Step C: Per-district forecasting
        # -----------------------------
        groups = list(df.groupby(["state", "district"]))

        # NOTE:
        # Multiprocessing kept for minimal code change.
        # Can be safely replaced with a for-loop if needed.
        num_cores = max(1, mp.cpu_count() - 1)
        logger.info(f"Using {num_cores} cores for parallel processing.")

        with mp.Pool(processes=num_cores) as pool:
            worker = partial(
                fit_single_district,
                horizon=self.horizon,
                value_col=value_col,
                global_growth=global_growth,
                growth_bounds=growth_bounds,
            )
            results_nested = pool.map(worker, groups)

        results = [r for sub in results_nested for r in sub]

        if results:
            pd.DataFrame(results).to_csv(output_file, index=False)
            logger.info(
                f"✅ {name} forecast ready ({len(results)} predictions)"
            )
        else:
            logger.warning(f"No forecasts generated for {name}")

    def run(self):
        logger.info("Starting Hierarchical Trend-Based Forecasting Pipeline...")

        tasks = [
            ("enrolment_features.csv", "total_enrolment", "Enrolment", "enrolment_forecast.csv"),
            ("demographic_features.csv", "total_updates", "Demographic", "demographic_forecast.csv"),
            ("biometric_features.csv", "total_biometric", "Biometric", "biometric_forecast.csv"),
        ]

        for feat_file, val_col, name, out_file in tasks:
            path = os.path.join(self.features_dir, feat_file)
            if os.path.exists(path):
                df = pd.read_csv(path)
                df["month"] = pd.to_datetime(df["month"])
                self.forecast_series(
                    df, val_col, name,
                    os.path.join(self.forecasts_dir, out_file)
                )

        logger.info("Forecasting Pipeline Completed Successfully.")


if __name__ == "__main__":
    Forecaster().run()
