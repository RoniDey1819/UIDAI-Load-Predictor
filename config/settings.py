import os

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Data directories
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
FEATURES_DATA_DIR = os.path.join(DATA_DIR, "features")

# Raw Data Subdirectories
RAW_DATA_SUBDIRS = {
    "enrolment": os.path.join(RAW_DATA_DIR, "api_data_aadhar_enrolment"),
    "demographic": os.path.join(RAW_DATA_DIR, "api_data_aadhar_demographic"),
    "biometric": os.path.join(RAW_DATA_DIR, "api_data_aadhar_biometric"),
}

# Expected Schemas (for validation)
# Based on inspection of raw files
SCHEMAS = {
    "enrolment": [
        "date", "state", "district", "pincode", 
        "age_0_5", "age_5_17", "age_18_greater"
    ],
    "demographic": [
        "date", "state", "district", "pincode", 
        "demo_age_5_17", "demo_age_17_"
    ],
    "biometric": [
        "date", "state", "district", "pincode", 
        "bio_age_5_17", "bio_age_17_"
    ]
}

# Data Settings
DATE_FORMAT = "%d-%m-%Y"  # Format observed: 01-03-2025

# Model directory
MODELS_DIR = os.path.join(BASE_DIR, "models")
