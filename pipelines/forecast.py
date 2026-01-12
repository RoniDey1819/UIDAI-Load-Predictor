import os
import pandas as pd
import numpy as np
import logging
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
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

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fit_single_district(group_data, horizon, value_col):
    """
    Helper function for parallel processing. Fits the best model for a single district.
    """
    state_district, group = group_data
    state, district = state_district
    
    try:
        group = group.sort_values('month')
        series = group.set_index('month')[value_col]
        
        # Ensure frequency
        if series.index.freq is None:
            series.index.freq = pd.infer_freq(series.index)
        
        n = len(series)
        pred = None
        
        # --- Model Selection Logic ---
        # Prioritize robustness for short data (~12 months)
        if n >= 24:
            # SARIMA for long series with seasonality
            try:
                model = SARIMAX(series, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12), 
                                enforce_stationarity=False, enforce_invertibility=False)
                res = model.fit(disp=False)
                pred = res.forecast(steps=horizon)
            except:
                n = 23 # Fallback to ETS
                
        if pred is None and n >= 12:
            # Exponential Smoothing (Holt-Winters) is more stable for 12-24 months
            try:
                model = ExponentialSmoothing(series, seasonal_periods=min(12, n-1), trend='add', seasonal='add')
                res = model.fit()
                pred = res.forecast(horizon)
            except:
                n = 11 # Fallback to simple ARIMA

        if pred is None and n >= 6:
            # Simple ARIMA/Damping for 6-12 months
            try:
                model = ARIMA(series, order=(1, 1, 0))
                res = model.fit()
                pred = res.forecast(steps=horizon)
            except:
                pred = None # Fallback to mean

        # Fallback to Moving Average / Mean
        if pred is None:
            mean_val = series.mean()
            pred = pd.Series([mean_val] * horizon)

        # --- Spike Mitigation (Clipping) ---
        # Cap forecast at 2x the historical maximum to prevent wild spikes
        hist_max = series.max()
        pred = np.clip(pred, 0, hist_max * 2)

        # Prepare Future Dates
        last_date = series.index[-1]
        future_dates = pd.date_range(start=last_date, periods=horizon+1, freq='M')[1:]
        
        results = []
        for i, (date, val) in enumerate(zip(future_dates, pred)):
            results.append({
                'state': state,
                'district': district,
                'month': date.date(),
                'forecast_value': max(0, int(val))
            })
        return results

    except Exception as e:
        return []

class Forecaster:
    """
    Optimized Forecasting engine using parallel processing and robust models.
    """
    
    def __init__(self):
        self.features_dir = settings.FEATURES_DATA_DIR
        self.forecasts_dir = os.path.join(settings.DATA_DIR, "forecasts")
        os.makedirs(self.forecasts_dir, exist_ok=True)
        self.horizon = 6

    def forecast_series(self, df, value_col, name, output_file):
        logger.info(f"Forecasting {name} (Parallel Optimized)...")
        
        # Prepare groups
        groups = list(df.groupby(['state', 'district']))
        total_groups = len(groups)
        
        # Parallel Execution
        num_cores = max(1, mp.cpu_count() - 1)
        logger.info(f"Using {num_cores} cores for parallel processing.")
        
        with mp.Pool(processes=num_cores) as pool:
            # Use partial to pass extra arguments
            worker_func = partial(fit_single_district, horizon=self.horizon, value_col=value_col)
            results_nested = pool.map(worker_func, groups)
            
        # Flatten results
        results = [item for sublist in results_nested for item in sublist]
        
        if results:
            res_df = pd.DataFrame(results)
            res_df.to_csv(output_file, index=False)
            logger.info(f"✅ {name} Forecast ready: {os.path.basename(output_file)} ({len(res_df)} predictions)")
        else:
            logger.warning(f"No results generated for {name}")

    def run(self):
        logger.info("Starting Parallel Forecasting Pipeline...")

        # Process each domain
        tasks = [
            ('enrolment_features.csv', 'total_enrolment', 'Enrolment', 'enrolment_forecast.csv'),
            ('demographic_features.csv', 'total_updates', 'Demographic', 'demographic_forecast.csv'),
            ('biometric_features.csv', 'total_biometric', 'Biometric', 'biometric_forecast.csv')
        ]

        for feat_file, val_col, name, out_file in tasks:
            path = os.path.join(self.features_dir, feat_file)
            if os.path.exists(path):
                df = pd.read_csv(path)
                df['month'] = pd.to_datetime(df['month'])
                self.forecast_series(df, val_col, name, os.path.join(self.forecasts_dir, out_file))

        logger.info("Forecasting Pipeline Completed Successfully.")

if __name__ == "__main__":
    Forecaster().run()
