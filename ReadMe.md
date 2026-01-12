# UIDAI Load Predictor

A production-grade predictive analytics and forecasting system for UIDAI Aadhaar infrastructure planning. This system forecasts demand for enrolments and updates (demographic and biometric) at the district level and generates automated infrastructure scaling recommendations.

## 🚀 Key Features

- **Domain-Specific Forecasting**: Independent SARIMA/ARIMA models for Enrolment, Demographic, and Biometric datasets.
- **Interactive Dashboard**: Modern React-based interface with Plotly.js for dynamic visualization.
- **District-Level Insights**: Monthly forecasts with state and district-level granularity.
- **Infrastructure Engine**: Automated recommendation system for Aadhaar center deployment.
- **RESTful API**: High-performance FastAPI backend serving real-time analytics.

## 📁 Project Structure

```
UIDAI Load Predictor/
├── data/
│   ├── raw/                    # Source CSV data
│   ├── processed/              # Cleaned & aggregated datasets
│   ├── features/               # Engineered time-series features
│   └── forecasts/              # SARIMA/ARIMA prediction outputs
├── pipelines/
│   ├── ingest.py               # Data ingestion
│   ├── clean.py                # Data cleaning & validation
│   ├── aggregate.py            # Monthly domain-specific aggregation
│   ├── feature_engineering.py  # Feature calculation (seasonality, spikes)
│   ├── forecast.py             # SARIMA/ARIMA forecasting engine
│   ├── recommend.py            # Infrastructure recommendation logic
│   └── validate.py             # Data integrity & schema validator
├── api/
│   └── main.py                 # FastAPI backend implementation
├── dashboard/                  # React + Vite frontend application
│   └── src/
│       ├── components/         # Interactive UI components (Heatmap, Charts)
│       ├── services/           # Backend API integration service
│       └── App.jsx             # Main dashboard logic & layout
├── config/
│   └── settings.py             # Global project configuration
├── run_pipeline.py             # Master ETL Pipeline Orchestrator
└── run_dashboard.bat           # One-click Launcher (API + Dashboard)
```

## 🛠️ Installation

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Backend Setup
```bash
pip install -r requirements.txt
```

### 2. Frontend Setup
```bash
cd dashboard
npm install
```

### 3. Docker Setup (Recommended)
You can run the entire application (Backend + Frontend) using Docker:
```bash
docker-compose up --build
```
This will start:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000

## 🏃 Usage


### Running the Data Pipeline
To process raw data and generate fresh forecasts across all domains:
```bash
python run_pipeline.py
```
*Tip: Run `python pipelines/validate.py` anytime to verify data integrity.*

### Launching the Dashboard
The easiest way to start both the API and the Web UI is via the launcher:
```powershell
.\run_dashboard.bat
```
- **Web UI**: `http://localhost:5173`
- **API Docs**: `http://localhost:8000/docs`

## 📊 Dashboard Highlights

- **Interactive Heatmap**: Visualizes infrastructure pressure across districts. Click any cell to drill down.
- **Dynamic Forecast Charts**: Explore 6-month predictions with zoom/pan capabilities.
- **Infrastructure Plans**: View recommended scaling actions for selected districts based on biometric/enrolment load.
- **Region Filtering**: Easily toggle between national views, state rankings, and specific district trends.

## ⚖️ Architectural Constraints
⚠️ **Strict Domain Separation**: As per system requirements, data from Enrolment, Demographic, and Biometric domains are processed through entirely independent ML pipelines. Data is combined **exclusively** at the final recommendation layer to ensure unbiased forecasting models.

## 🏗️ Technology Stack
- **AI/ML**: Statsmodels (SARIMA/ARIMA), Pandas, NumPy
- **Backend**: FastAPI, Uvicorn
- **Frontend**: React 18, Vite, Plotly.js, Axios
- **Orchestration**: Python-based subprocess management

## 📜 License
Developed for the UIDAI Aadhaar Hackathon analytics challenge.
