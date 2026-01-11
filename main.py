import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from src.pipeline import build_mid_master_df
from src.forecast import generate_forecasts
from src.analytics import calculate_derived_indicators, generate_recommendations

def main():
    base_dir = os.getcwd()
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    print("--- Starting Aadhaar Infrastructure Analytics ---")

    # 1. Run Data Pipeline
    print("\n[1/4] Building Master Dataset...")
    master_df = build_mid_master_df(base_dir)
    master_csv_path = os.path.join(output_dir, "master_dataset_monthly.csv")
    master_df.to_csv(master_csv_path, index=False)
    print(f"Master Dataset created at: {master_csv_path}")

    # 2. Generate Forecasts
    print("\n[2/4] Generating Forecasts...")
    forecast_df = generate_forecasts(master_df)
    forecast_csv_path = os.path.join(output_dir, "district_forecasts.csv")
    forecast_df.to_csv(forecast_csv_path, index=False)
    print(f"Forecasts generated at: {forecast_csv_path}")

    # 3. Infrastructure Recommendations
    print("\n[3/4] Generating Infrastructure Plan...")
    # Aggregate to get average demand over forecast horizon
    avg_fc_df = forecast_df.groupby(['state', 'district'])[
        ['Forecast_Enrolment', 'Forecast_Bio_Updates', 'Forecast_Demo_Updates']
    ].mean().reset_index()

    indicators_df = calculate_derived_indicators(avg_fc_df)
    plan_df = generate_recommendations(indicators_df)
    
    plan_csv_path = os.path.join(output_dir, "infrastructure_plan.csv")
    plan_df.to_csv(plan_csv_path, index=False)
    print(f"Infrastructure Plan generated at: {plan_csv_path}")
    
    # 4. Visualizations
    print("\n[4/4] Creating Visualizations...")
    # Filter for top 20 districts by Update Stress Score
    top_stress = plan_df.sort_values('Update_Stress_Score', ascending=False).head(20)

    plt.figure(figsize=(12, 6))
    sns.barplot(data=top_stress, x='Update_Stress_Score', y='district', hue='state', dodge=False)
    plt.title('Top 20 Districts by Biometric Update Stress')
    plt.xlabel('Stress Score (0-100)')
    plt.tight_layout()
    
    viz_path = os.path.join(output_dir, "top_stress_districts.png")
    plt.savefig(viz_path)
    print(f"Visualization saved to: {viz_path}")
    print("\n--- Analysis Complete! ---")
    print(f"Check the '{output_dir}' folder for results.")

if __name__ == "__main__":
    main()
