import React, { useState, useEffect } from 'react';
import { getStates, getDistricts, getForecasts, getRecommendations, getHeatmapData } from './services/api';
import Heatmap from './components/Heatmap';
import ForecastChart from './components/ForecastChart';
import RecommendationCard from './components/RecommendationCard';
import './App.css';

function App() {
  const [states, setStates] = useState([]);
  const [districts, setDistricts] = useState([]);

  // Filters
  const [selectedState, setSelectedState] = useState('');
  const [selectedDistrict, setSelectedDistrict] = useState('');
  const [heatmapType, setHeatmapType] = useState('biometric');

  // Data
  const [heatmapData, setHeatmapData] = useState([]);
  const [enrolmentData, setEnrolmentData] = useState([]);
  const [demographicData, setDemographicData] = useState([]);
  const [biometricData, setBiometricData] = useState([]);
  const [recommendations, setRecommendations] = useState([]);

  const [loading, setLoading] = useState(true);

  // Load States on mount
  useEffect(() => {
    getStates().then(setStates).catch(err => console.error("Failed to load states", err));
  }, []);

  // Load Heatmap Data when Type or State changes
  useEffect(() => {
    setLoading(true);
    getHeatmapData(heatmapType, selectedState)
      .then(data => {
        setHeatmapData(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Heatmap load fail", err);
        setLoading(false);
      });
  }, [heatmapType, selectedState]);

  // Load Districts when State changes
  useEffect(() => {
    if (selectedState) {
      getDistricts(selectedState).then(setDistricts);
      setSelectedDistrict('');
    } else {
      setDistricts([]);
      setSelectedDistrict('');
    }
  }, [selectedState]);

  // Load Chart & Recommendation Data
  useEffect(() => {
    if (selectedState || selectedDistrict) {
      const loadData = async () => {
        try {
          const [enrol, demo, bio, recs] = await Promise.all([
            getForecasts('enrolment', selectedState, selectedDistrict),
            getForecasts('demographic', selectedState, selectedDistrict),
            getForecasts('biometric', selectedState, selectedDistrict),
            getRecommendations(selectedState, selectedDistrict)
          ]);

          setEnrolmentData(enrol);
          setDemographicData(demo);
          setBiometricData(bio);
          setRecommendations(recs);
        } catch (e) {
          console.error("Chart data load fail", e);
        }
      };
      loadData();
    }
  }, [selectedState, selectedDistrict]);

  const handleHeatmapClick = (district) => {
    const point = heatmapData.find(d => d.district === district);
    if (point) {
      setSelectedState(point.state);
      // We set timeout to allow the districts to load before selecting one
      setTimeout(() => setSelectedDistrict(district), 100);
    }
  };

  const clearFilters = () => {
    setSelectedState('');
    setSelectedDistrict('');
    setEnrolmentData([]);
    setDemographicData([]);
    setBiometricData([]);
    setRecommendations([]);
  };

  return (
    <div className="app-container">
      <header className="header">
        <div className="header-content">
          <h1>UIDAI Load Predictor</h1>
          <p className="subtitle">Infrastructure Planning & Demand Forecasting Dashboard</p>
        </div>
      </header>

      <div className="dashboard-controls">
        <div className="filter-group">
          <label>Region Filter</label>
          <div className="select-row">
            <select value={selectedState} onChange={(e) => setSelectedState(e.target.value)}>
              <option value="">All States</option>
              {states.map(s => <option key={s} value={s}>{s}</option>)}
            </select>

            <select value={selectedDistrict} onChange={(e) => setSelectedDistrict(e.target.value)} disabled={!selectedState}>
              <option value="">All Districts</option>
              {districts.map(d => <option key={d} value={d}>{d}</option>)}
            </select>

            <button onClick={clearFilters} className="btn-clear">
              Reset Filters
            </button>
          </div>
        </div>

        <div className="filter-group">
          <label>Heatmap Pressure Metric</label>
          <div className="tab-group">
            {['enrolment', 'demographic', 'biometric'].map(type => (
              <button
                key={type}
                className={`tab-btn ${heatmapType === type ? 'active' : ''}`}
                onClick={() => setHeatmapType(type)}
              >
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      <main className="dashboard-grid">
        <section className="section heatmap-section">
          <div className="section-header">
            <h2>{selectedState ? `Demand in ${selectedState}` : 'National Demand Intensity'}</h2>
            <span>Click a district cell to drill down into detailed trends</span>
          </div>
          {loading ? (
            <div className="loading-state">Syncing forecast data...</div>
          ) : (
            <Heatmap
              data={heatmapData}
              title={`${heatmapType.charAt(0).toUpperCase() + heatmapType.slice(1)} Forecast Matrix`}
              onDistrictSelect={handleHeatmapClick}
            />
          )}
        </section>

        <div className="details-grid">
          <section className="section charts-section">
            <div className="section-header">
              <h2>Forecasted Load Trends</h2>
              <span className="location-tag">
                {selectedDistrict ? `District: ${selectedDistrict}` : (selectedState ? `State: ${selectedState}` : 'Select a region to see trends')}
              </span>
            </div>
            <div className="charts-container">
              <ForecastChart data={enrolmentData} type="enrolment" title="Enrolment Volume" />
              <ForecastChart data={demographicData} type="demographic" title="Demographic Updates" />
              <ForecastChart data={biometricData} type="biometric" title="Biometric Updates" />
            </div>
          </section>

          <section className="section recs-section">
            <div className="section-header">
              <h2>Infrastructure Recommendations</h2>
            </div>
            <div className="recs-grid">
              {recommendations.slice(0, 8).map((rec, idx) => (
                <RecommendationCard key={idx} recommendation={rec} />
              ))}
              {recommendations.length === 0 && (
                <div className="empty-state">Select a state or district to generate infrastructure scaling plans.</div>
              )}
            </div>
          </section>
        </div>
      </main>

      <footer className="footer">
        <p>UIDAI Aadhaar Hackathon - Predictive Analytics Engine</p>
      </footer>
    </div>
  );
}

export default App;
