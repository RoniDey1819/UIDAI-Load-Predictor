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
def fit_single_district(group_data, horizon, value_col, global_growth):
    """
    Trend-based, bounded extrapolation for a single district.
    Falls back to global (cross-region) growth when local data is weak.
    """
    (state, district), group = group_data

    try:
        group = group.sort_values("month")
        y = group[value_col].values
        n = len(y)

        # -----------------------------
        # Step 1: Estimate local trend
        # -----------------------------
        if n >= 3:
            x = np.arange(n)
            slope, intercept = np.polyfit(x, y, 1)
            growth_rate = slope / max(y.mean(), 1)
        else:
            # Too little data → borrow from global behavior
            growth_rate = global_growth

        # -----------------------------
        # Step 2: Bound growth (CRITICAL)
        # -----------------------------
        growth_rate = np.clip(growth_rate, -0.05, 0.20)

        # -----------------------------
        # Step 3: Extrapolate
        # -----------------------------
        last_val = y[-1]
        preds = []
        current = last_val

        for _ in range(horizon):
            current = current * (1 + growth_rate)
            preds.append(max(0, current))

        # -----------------------------
        # Prepare output
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

    except Exception:
        return []


# -----------------------------------------------------------------------------
# Forecaster
# -----------------------------------------------------------------------------
class Forecaster:
    """
    Trend-based forecasting engine using cross-region growth borrowing.
    """

    def __init__(self):
        self.features_dir = settings.FEATURES_DATA_DIR
        self.forecasts_dir = os.path.join(settings.DATA_DIR, "forecasts")
        os.makedirs(self.forecasts_dir, exist_ok=True)
        self.horizon = 6

    def forecast_series(self, df, value_col, name, output_file):
        logger.info(f"Forecasting {name} using trend-based extrapolation...")

        # -----------------------------
        # Cross-region growth estimate
        # -----------------------------
        valid = df[df[value_col] > 0]
        if len(valid) >= 3:
            x = np.arange(len(valid))
            global_slope, _ = np.polyfit(x, valid[value_col].values, 1)
            global_growth = global_slope / max(valid[value_col].mean(), 1)
        else:
            global_growth = 0.0

        global_growth = np.clip(global_growth, -0.05, 0.15)

        groups = list(df.groupby(["state", "district"]))

        num_cores = max(1, mp.cpu_count() - 1)
        logger.info(f"Using {num_cores} cores for parallel processing.")

        with mp.Pool(processes=num_cores) as pool:
            worker = partial(
                fit_single_district,
                horizon=self.horizon,
                value_col=value_col,
                global_growth=global_growth,
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
        logger.info("Starting Trend-Based Forecasting Pipeline...")

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
