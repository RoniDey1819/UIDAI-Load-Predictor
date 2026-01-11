import pandas as pd
import numpy as np

def calculate_derived_indicators(forecast_df):
    """
    Calculates Stress Scores and Indices based on Forecasted Demand.
    """
    df = forecast_df.copy()
    
    # 1. Enrolment Growth Proxy (Normalized)
    # Since we only have forecast values here, we'll use magnitude as proxy for load
    load_max = df['Forecast_Enrolment'].max()
    if load_max > 0:
        df['Enrolment_Load_Index'] = (df['Forecast_Enrolment'] / load_max) * 100
    else:
        df['Enrolment_Load_Index'] = 0

    # 2. Update Load Index
    # Weighted sum: Bio updates usually take longer than Demographics
    # Weight: Bio=1.5, Demo=1.0
    df['Weighted_Update_Load'] = (df['Forecast_Bio_Updates'] * 1.5) + df['Forecast_Demo_Updates']
    
    update_max = df['Weighted_Update_Load'].max()
    if update_max > 0:
        df['Update_Stress_Score'] = (df['Weighted_Update_Load'] / update_max) * 100
    else:
        df['Update_Stress_Score'] = 0
        
    return df

def generate_recommendations(analytics_df):
    """
    Recommends infrastructure based on Stress Scores.
    Assumptions:
    - 1 Enrolment Kit can handle ~30 enrolments/day => ~750/month (25 working days)
    - 1 Update Kit can handle ~40 updates/day => ~1000/month
    """
    df = analytics_df.copy()
    
    # Constants
    ENROL_CAPACITY_PER_MONTH = 750
    UPDATE_CAPACITY_PER_MONTH = 1000
    
    # Calculate Required Kits (Round up)
    df['Rec_Enrolment_Kits'] = np.ceil(df['Forecast_Enrolment'] / ENROL_CAPACITY_PER_MONTH)
    df['Rec_Update_Kits'] = np.ceil(df['Weighted_Update_Load'] / UPDATE_CAPACITY_PER_MONTH)
    
    # Classification
    def classify_zone(row):
        if row['Update_Stress_Score'] > 75 and row['Enrolment_Load_Index'] > 75:
            return "Critical High Demand"
        elif row['Update_Stress_Score'] > 75:
            return "Update Heavy Zone"
        elif row['Enrolment_Load_Index'] > 75:
            return "Enrolment Heavy Zone"
        else:
            return "Normal"
            
    df['Zone_Category'] = df.apply(classify_zone, axis=1)
    
    return df

if __name__ == "__main__":
    import os
    try:
        fc_path = os.path.join(os.getcwd(), "output", "district_forecasts.csv")
        if os.path.exists(fc_path):
            df = pd.read_csv(fc_path)
            
            # For analytics, we might want to aggregate forecasts (e.g., average over the next 6 months)
            # or just take the peak month. Let's take the AVERAGE demand over the forecast horizon for planning.
            avg_df = df.groupby(['state', 'district'])[[
                'Forecast_Enrolment', 'Forecast_Bio_Updates', 'Forecast_Demo_Updates'
            ]].mean().reset_index()
            
            indicators_df = calculate_derived_indicators(avg_df)
            rec_df = generate_recommendations(indicators_df)
            
            output_path = os.path.join(os.getcwd(), "output", "infrastructure_plan.csv")
            rec_df.to_csv(output_path, index=False)
            print("Infrastructure Plan generated successfully.")
            print(rec_df.head())
        else:
            print("Forecasts not found. Run forecast.py first.")
    except Exception as e:
        print(f"Analytics Failed: {e}")
