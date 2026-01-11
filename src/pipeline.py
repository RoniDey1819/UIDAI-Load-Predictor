import pandas as pd
import glob
import os

def load_dataset(directory_path, date_col='date'):
    """
    Loads all CSV files from a directory and concatenates them.
    Assumes a common schema for all CSVs in the folder.
    """
    all_files = glob.glob(os.path.join(directory_path, "*.csv"))
    
    if not all_files:
        print(f"Warning: No files found in {directory_path}")
        return pd.DataFrame()

    df_list = []
    for filename in all_files:
        try:
            # Low_memory=False to handle mixed types if any, generic parser
            df = pd.read_csv(filename, low_memory=False)
            df_list.append(df)
        except Exception as e:
            print(f"Error reading {filename}: {e}")

    if not df_list:
        return pd.DataFrame()

    full_df = pd.concat(df_list, ignore_index=True)
    
    # Standardize Date Column
    # The EDA showed '01-03-2025', '09-03-2025' -> DD-MM-YYYY format
    if date_col in full_df.columns:
        full_df[date_col] = pd.to_datetime(full_df[date_col], format='%d-%m-%Y', errors='coerce')
        full_df = full_df.dropna(subset=[date_col])
    
    return full_df

def aggregate_to_monthly(df, value_cols, group_cols=['state', 'district', 'pincode']):
    """
    Aggregates daily data to monthly frequency.
    """
    if df.empty:
        return df
        
    df['month'] = df['date'].dt.to_period('M').dt.to_timestamp()
    
    # Ensure numeric columns are actually numeric
    for col in value_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    agg_dict = {col: 'sum' for col in value_cols}
    
    monthly_df = df.groupby(['month'] + group_cols).agg(agg_dict).reset_index()
    return monthly_df

def build_mid_master_df(base_dir):
    """
    Loads Enrolment, Bio Update, and Demo Update datasets, aggregates them, 
    and merges into a single master dataframe.
    """
    
    # 1. Load Enrolment
    print("Loading Enrolment Data...")
    enrol_path = os.path.join(base_dir, 'data', 'api_data_aadhar_enrolment')
    df_enrol = load_dataset(enrol_path)
    # Enrolment cols: age_0_5, age_5_17, age_18_greater
    enrol_val_cols = ['age_0_5', 'age_5_17', 'age_18_greater']
    df_enrol_monthly = aggregate_to_monthly(df_enrol, enrol_val_cols)
    df_enrol_monthly['Total_Enrolment'] = df_enrol_monthly[enrol_val_cols].sum(axis=1)

    # 2. Load Biometric Update
    print("Loading Biometric Update Data...")
    bio_path = os.path.join(base_dir, 'data', 'api_data_aadhar_biometric')
    df_bio = load_dataset(bio_path)
    # Bio cols: bio_age_5_17, bio_age_17_ (Note: EDA showed 'bio_age_17_' is likely 'bio_age_17_greater' truncated or similar)
    # Let's handle generic matching if column names vary slightly, but per EDA: 'bio_age_5_17', 'bio_age_17_'
    bio_val_cols = ['bio_age_5_17', 'bio_age_17_']
    df_bio_monthly = aggregate_to_monthly(df_bio, bio_val_cols)
    df_bio_monthly['Total_Biometric_Updates'] = df_bio_monthly[bio_val_cols].sum(axis=1)

    # 3. Load Demographic Update
    print("Loading Demographic Update Data...")
    demo_path = os.path.join(base_dir, 'data', 'api_data_aadhar_demographic')
    df_demo = load_dataset(demo_path)
    # Demo cols: demo_age_5_17, demo_age_17_
    demo_val_cols = ['demo_age_5_17', 'demo_age_17_']
    df_demo_monthly = aggregate_to_monthly(df_demo, demo_val_cols)
    df_demo_monthly['Total_Demographic_Updates'] = df_demo_monthly[demo_val_cols].sum(axis=1)

    # 4. Merge
    print("Merging Datasets...")
    # Outer join to keep all pincodes/months
    merge_cols = ['month', 'state', 'district', 'pincode']
    
    master_df = pd.merge(df_enrol_monthly, df_bio_monthly, on=merge_cols, how='outer', suffixes=('_enrol', '_bio'))
    master_df = pd.merge(master_df, df_demo_monthly, on=merge_cols, how='outer')
    
    # Fill NAs with 0
    master_df = master_df.fillna(0)
    
    return master_df

if __name__ == "__main__":
    # Test run
    base_dir = os.getcwd()
    try:
        df = build_mid_master_df(base_dir)
        print("Master DataFrame Built Successfully")
        print(df.head())
        print(f"Total Rows: {len(df)}")
        df.to_csv(os.path.join(base_dir, "output", "master_dataset_monthly.csv"), index=False)
    except Exception as e:
        print(f"Pipeline Failed: {e}")
