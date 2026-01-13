from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
import logging
from typing import List, Optional, Dict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="UIDAI Load Predictor API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
FORECAST_DIR = os.path.join(DATA_DIR, "forecasts")
FEATURES_DIR = os.path.join(DATA_DIR, "features")

# In-memory cache for data
data_cache = {}

def load_data(file_path):
    """Loads CSV data with caching and basic validation."""
    if file_path in data_cache:
        # Check file modification time to see if we should reload
        if os.path.getmtime(file_path) <= data_cache[file_path]['mtime']:
            return data_cache[file_path]['df']
    
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return None
        
    try:
        df = pd.read_csv(file_path)
        if 'month' in df.columns:
            df['month'] = pd.to_datetime(df['month'])
        
        data_cache[file_path] = {
            'df': df,
            'mtime': os.path.getmtime(file_path)
        }
        return df
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return None

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "UIDAI Load Predictor API",
        "version": "1.0.0"
    }

@app.get("/api/health")
def health_check():
    """Health check endpoint for Docker and monitoring."""
    return {"status": "healthy"}

@app.get("/api/meta")
def get_meta():
    """Returns metadata about the available data (last update, row counts)."""
    meta = {}
    files = {
        "enrolment": os.path.join(FORECAST_DIR, "enrolment_forecast.csv"),
        "demographic": os.path.join(FORECAST_DIR, "demographic_forecast.csv"),
        "biometric": os.path.join(FORECAST_DIR, "biometric_forecast.csv"),
        "recommendations": os.path.join(DATA_DIR, "recommendations.csv")
    }
    
    for key, path in files.items():
        if os.path.exists(path):
            df = load_data(path)
            meta[key] = {
                "rows": len(df) if df is not None else 0,
                "last_update": pd.Timestamp(os.path.getmtime(path), unit='s').strftime('%Y-%m-%d %H:%M:%S')
            }
    return meta

@app.get("/api/states")
def get_states():
    df = load_data(os.path.join(FORECAST_DIR, "enrolment_forecast.csv"))
    if df is None:
        return {"states": []}
    return {"states": sorted(df['state'].unique().tolist())}

@app.get("/api/districts/{state}")
def get_districts(state: str):
    df = load_data(os.path.join(FORECAST_DIR, "enrolment_forecast.csv"))
    if df is None:
        return {"districts": []}
    districts = df[df['state'] == state]['district'].unique().tolist()
    return {"districts": sorted(districts)}

@app.get("/api/forecasts/{type}")
def get_forecasts(type: str, state: Optional[str] = None, district: Optional[str] = None):
    if type not in ['enrolment', 'demographic', 'biometric']:
        raise HTTPException(status_code=400, detail="Invalid forecast type")
        
    # 1. Get Forecast Data
    forecast_filename = f"{type}_forecast.csv"
    forecast_filepath = os.path.join(FORECAST_DIR, forecast_filename)
    f_df = load_data(forecast_filepath)
    
    if f_df is None:
        raise HTTPException(status_code=404, detail=f"Forecast data for {type} not found")
        
    f_temp = f_df.copy()
    if state:
        f_temp = f_temp[f_temp['state'] == state]
    if district:
        f_temp = f_temp[f_temp['district'] == district]
    
    f_temp['is_forecast'] = True
    f_temp = f_temp.rename(columns={'forecast_value': 'value'})

    # 2. Get Historical Data (Last 6 months)
    hist_filename = f"{type}_monthly_agg.csv"
    hist_filepath = os.path.join(os.path.join(DATA_DIR, "processed"), hist_filename)
    h_df = load_data(hist_filepath)
    
    combined_data = []
    
    if h_df is not None:
        h_temp = h_df.copy()
        if state:
            h_temp = h_temp[h_temp['state'] == state]
        if district:
            h_temp = h_temp[h_temp['district'] == district]
            
        # Aggregate historical columns into 'value' based on type
        if type == 'enrolment':
            # Sum age groups
            h_temp['value'] = h_temp['age_0_5'] + h_temp['age_5_17'] + h_temp['age_18_greater']
        elif type == 'demographic':
            h_temp['value'] = h_temp['demo_age_5_17'] + h_temp['demo_age_17_']
        elif type == 'biometric':
            h_temp['value'] = h_temp['bio_age_5_17'] + h_temp['bio_age_17_']
            
        h_temp['is_forecast'] = False
        
        # Keep only necessary columns for the chart
        h_subset = h_temp[['state', 'district', 'month', 'value', 'is_forecast']].tail(6 * (len(h_temp['district'].unique()) if not district else 1))
        
        # If multiple districts are selected (only state filter), we need to aggregate them by month
        if state and not district:
            h_subset = h_subset.groupby(['state', 'month', 'is_forecast'])['value'].sum().reset_index()
            h_subset['district'] = "All"
        elif not state and not district:
            h_subset = h_subset.groupby(['month', 'is_forecast'])['value'].sum().reset_index()
            h_subset['state'] = "All"
            h_subset['district'] = "All"

        # Format month for JSON
        h_subset['month'] = h_subset['month'].dt.strftime('%Y-%m-%d')
        combined_data.extend(h_subset.to_dict(orient="records"))

    # Process Forecast data for aggregation if needed
    if state and not district:
        f_subset = f_temp.groupby(['state', 'month', 'is_forecast'])['value'].sum().reset_index()
        f_subset['district'] = "All"
    elif not state and not district:
        f_subset = f_temp.groupby(['month', 'is_forecast'])['value'].sum().reset_index()
        f_subset['state'] = "All"
        f_subset['district'] = "All"
    else:
        f_subset = f_temp[['state', 'district', 'month', 'value', 'is_forecast']]

    f_subset['month'] = f_subset['month'].dt.strftime('%Y-%m-%d')
    combined_data.extend(f_subset.to_dict(orient="records"))
        
    return combined_data

@app.get("/api/recommendations")
def get_recommendations(state: Optional[str] = None, district: Optional[str] = None):
    filepath = os.path.join(DATA_DIR, "recommendations.csv")
    df = load_data(filepath)
    
    if df is None:
        raise HTTPException(status_code=404, detail="Recommendations not found")
        
    temp_df = df.copy()
    if state:
        temp_df = temp_df[temp_df['state'] == state]
    if district:
        temp_df = temp_df[temp_df['district'] == district]
        
    return temp_df.to_dict(orient="records")

@app.get("/api/heatmap/{type}")
def get_heatmap_data(type: str, state: Optional[str] = None):
    """Returns aggregated data for heatmap, optionally filtered by state."""
    filename = f"{type}_forecast.csv"
    filepath = os.path.join(FORECAST_DIR, filename)
    df = load_data(filepath)
    
    if df is None:
        raise HTTPException(status_code=404, detail=f"Forecast data for {type} not found")
    
    temp_df = df.copy()
    if state:
        temp_df = temp_df[temp_df['state'] == state]
    
    if 'month' in temp_df.columns:
        temp_df['month'] = temp_df['month'].dt.strftime('%Y-%m-%d')
        
    return temp_df.to_dict(orient="records")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
