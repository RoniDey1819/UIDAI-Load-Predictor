import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import warnings

# Suppress convergence warnings for cleaner output
warnings.filterwarnings("ignore")

def train_forecast_model(data, target_col, periods=6):
    """
    Trains a Holt-Winters model on monthly data and forecasts 'periods' ahead.
    Input 'data' should be a Series with DatetimeIndex (monthly).
    """
    if len(data) == 0:
        return pd.Series([0]*periods)
        
    if len(data) < 4:
        # Not enough data for HW, return simple mean forecast
        mean_val = data.mean()
        return pd.Series([mean_val]*periods, index=pd.date_range(start=data.index[-1], periods=periods+1, freq='M')[1:])
    
    try:
        # Seasonal periods: 12 for annual seasonality
        # Use 'add' trend and seasonality if possible, fall back if data is strictly positive or has zeros
        # For robustness with potential zeros, we use additive.
        if len(data) >= 24: # Need 2 full cycles for decent seasonality
             model = ExponentialSmoothing(data, trend='add', seasonal='add', seasonal_periods=12).fit()
        else:
             # Fallback to simple smoothing if < 2 years data
             model = ExponentialSmoothing(data, trend='add').fit()
             
        forecast = model.forecast(periods)
        return forecast
    except Exception as e:
        # Fallback to mean if model fails
        return pd.Series([data.mean()]*periods, index=pd.date_range(start=data.index[-1], periods=periods+1, freq='M')[1:])

def generate_forecasts(master_df, forecast_horizon=6):
    """
    Generates forecasts for Enrolment and Updates for each District.
    (Aggregating to District level first to avoid sparse data at Pincode level for forecasting)
    """
    
    # 1. Aggregate to District Level (State, District, Month)
    # This reduces noise and improves forecast quality vs Pincode level
    district_df = master_df.groupby(['state', 'district', 'month'])[[
        'Total_Enrolment', 'Total_Biometric_Updates', 'Total_Demographic_Updates'
    ]].sum().reset_index()
    
    unique_districts = district_df[['state', 'district']].drop_duplicates()
    
    forecast_results = []
    
    print(f"Generating Forecasts for {len(unique_districts)} districts...")
    
    count = 0
    for _, row in unique_districts.iterrows():
        state = row['state']
        district = row['district']
        
        subset = district_df[(district_df['state'] == state) & (district_df['district'] == district)]
        if subset.empty:
            continue
            
        subset = subset.set_index('month').sort_index()
        
        # Ensure full date range (fill missing months with 0)
        start_date = subset.index.min()
        end_date = subset.index.max()
        
        if pd.isna(start_date) or pd.isna(end_date):
            continue
            
        all_months = pd.date_range(start=start_date, end=end_date, freq='M')
        subset = subset.reindex(all_months).fillna(0)
        
        # Forecast Enrolment
        enrol_fc = train_forecast_model(subset['Total_Enrolment'], 'Total_Enrolment', forecast_horizon)
        
        # Forecast Bio Updates
        bio_fc = train_forecast_model(subset['Total_Biometric_Updates'], 'Total_Biometric_Updates', forecast_horizon)
        
        # Forecast Demo Updates
        demo_fc = train_forecast_model(subset['Total_Demographic_Updates'], 'Total_Demographic_Updates', forecast_horizon)
        
        # Combine results
        # fc series index is FUTURE dates
        for date, val in enrol_fc.items():
            res = {
                'state': state,
                'district': district,
                'forecast_month': date,
                'Forecast_Enrolment': val,
                'Forecast_Bio_Updates': bio_fc[date],
                'Forecast_Demo_Updates': demo_fc[date]
            }
            forecast_results.append(res)
            
        count += 1
        if count % 50 == 0:
            print(f"Processed {count} districts...")
            
    results_df = pd.DataFrame(forecast_results)
    
    # Clip negative forecasts to 0 (cannot have negative traffic)
    num_cols = ['Forecast_Enrolment', 'Forecast_Bio_Updates', 'Forecast_Demo_Updates']
    results_df[num_cols] = results_df[num_cols].clip(lower=0)
    
    return results_df

if __name__ == "__main__":
    # Test run
    try:
        master_path = os.path.join(os.getcwd(), "output", "master_dataset_monthly.csv")
        if os.path.exists(master_path):
            df = pd.read_csv(master_path, parse_dates=['month'])
            fc_df = generate_forecasts(df)
            output_path = os.path.join(os.getcwd(), "output", "district_forecasts.csv")
            fc_df.to_csv(output_path, index=False)
            print("Forecasts generated successfully.")
            print(fc_df.head())
        else:
            print("Master dataset not found. Run pipeline.py first.")
    except Exception as e:
        print(f"Forecasting Failed: {e}")
