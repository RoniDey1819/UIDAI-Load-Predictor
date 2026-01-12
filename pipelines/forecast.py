import os
import pandas as pd
import numpy as np
import logging
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.arima.model import ARIMA
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

class Forecaster:
    """
    Forecasting engine that predicts future volume for each domain independently.
    Strictly uses SARIMA / ARIMA models as per requirements.
    """
    
    def __init__(self):
        self.features_dir = settings.FEATURES_DATA_DIR
        self.forecasts_dir = os.path.join(settings.DATA_DIR, "forecasts")
        os.makedirs(self.forecasts_dir, exist_ok=True)
        self.horizon = 6 # Forecast 6 months ahead (Request says 3-12, picking 6 for balance)

    def fit_and_forecast(self, series):
        """
        Fits SARIMA/ARIMA model and returns forecast.
        Prioritizes SARIMA(1,0,0)(0,0,0,12) for seasonality if data permits.
        Falls back to ARIMA or simple mean for very short series.
        """
        model = None
        pred = None
        
        # Ensure series has a frequency
        if series.index.freq is None:
            try:
                series.index.freq = pd.infer_freq(series.index)
            except:
                pass
        
        # Hard constraint: Check length
        n = len(series)
        
        try:
            if n >= 24:
                # Use SARIMA with annual seasonality
                model = SARIMAX(series, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12), 
                                enforce_stationarity=False, enforce_invertibility=False)
                res = model.fit(disp=False)
                pred = res.forecast(steps=self.horizon)
            elif n >= 12:
                # Use standard ARIMA
                model = ARIMA(series, order=(1, 1, 1))
                res = model.fit()
                pred = res.forecast(steps=self.horizon)
            elif n >= 6:
                # Simple ARIMA
                model = ARIMA(series, order=(1, 0, 0))
                res = model.fit()
                pred = res.forecast(steps=self.horizon)
            else:
                pass 
        except Exception as e:
            pass

        # Prepare Future Dates
        last_date = series.index[-1]
        future_dates = pd.date_range(start=last_date, periods=self.horizon+1, freq='M')[1:]

        if pred is not None:
             # Ensure pred has correct date index if it lost it or is RangeIndex
             # Only assign if lenghts match
            try:
                if len(pred) == len(future_dates):
                    pred = pd.Series(pred.values, index=future_dates)
            except:
                pred = None # Fallback if something weird happened

        if pred is None:
            # Fallback for failures or short data
            mean_val = series.mean()
            pred = pd.Series([mean_val]*self.horizon, index=future_dates)

        return pred

    def forecast_series(self, df, value_col, name, output_file):
        logger.info(f"Forecasting {name} (SARIMA/ARIMA)...")
        results = []
        
        # Group by district
        groups = df.groupby(['state', 'district'])
        count = 0
        total_groups = len(groups)
        
        for (state, district), group in groups:
            try:
                # Sort by date
                group = group.sort_values('month')
                series = group.set_index('month')[value_col]
                
                # Fit Model
                pred = self.fit_and_forecast(series)
                
                # Collect results
                for date, val in pred.items():
                    results.append({
                        'state': state,
                        'district': district,
                        'month': date.date(), # Store as date only
                        'forecast_value': max(0, int(val)) # No negative forecasts
                    })
                    
            except Exception as e:
                if count % 100 == 0:
                    logger.warning(f"Error forecasting {state}-{district}: {str(e)}")
            
            count += 1
            if count % 100 == 0 or count == total_groups:
                percent = (count / total_groups) * 100
                logger.info(f"Progress ({name}): {count}/{total_groups} districts ({percent:.1f}%)")

        # Save results
        if results:
            res_df = pd.DataFrame(results)
            # Ensure folder exists
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            res_df.to_csv(output_file, index=False)
            logger.info(f"✅ {name} Forecast ready: {os.path.basename(output_file)} ({len(res_df)} predictions)")
        else:
            logger.warning(f"No results generated for {name}")

    def run(self):
        logger.info("Starting Separate Forecasting Models (Step 5 - SARIMA/ARIMA)...")

        # 1. Enrolment Forecast
        enrol_path = os.path.join(self.features_dir, "enrolment_features.csv")
        if os.path.exists(enrol_path):
            enrol_df = pd.read_csv(enrol_path)
            enrol_df['month'] = pd.to_datetime(enrol_df['month'])
            self.forecast_series(enrol_df, 'total_enrolment', 'Enrolment', 
                                os.path.join(self.forecasts_dir, "enrolment_forecast.csv"))

        # 2. Demographic Update Forecast
        demo_path = os.path.join(self.features_dir, "demographic_features.csv")
        if os.path.exists(demo_path):
            demo_df = pd.read_csv(demo_path)
            demo_df['month'] = pd.to_datetime(demo_df['month'])
            self.forecast_series(demo_df, 'total_updates', 'Demographic', 
                                os.path.join(self.forecasts_dir, "demographic_forecast.csv"))

        # 3. Biometric Update Forecast
        bio_path = os.path.join(self.features_dir, "biometric_features.csv")
        if os.path.exists(bio_path):
            bio_df = pd.read_csv(bio_path)
            bio_df['month'] = pd.to_datetime(bio_df['month'])
            self.forecast_series(bio_df, 'total_biometric', 'Biometric', 
                                os.path.join(self.forecasts_dir, "biometric_forecast.csv"))
                                
        logger.info("Step 5 (Forecasting) Completed Successfully.")

if __name__ == "__main__":
    Forecaster().run()
