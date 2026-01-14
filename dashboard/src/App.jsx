import React, { useState, useEffect } from 'react';
import { getStates, getDistricts, getForecasts, getRecommendations } from './services/api';
import HighDemandMap from './components/HighDemandMap';
import ForecastChart from './components/ForecastChart';
import RecommendationCard from './components/RecommendationCard';
import './App.css';

function App() {
  const [states, setStates] = useState([]);
  const [districts, setDistricts] = useState([]);

  // Filters
  const [selectedState, setSelectedState] = useState('');
  const [selectedDistrict, setSelectedDistrict] = useState('');

  // Data
  const [enrolmentData, setEnrolmentData] = useState([]);
  const [demographicData, setDemographicData] = useState([]);
  const [biometricData, setBiometricData] = useState([]);
  const [recommendations, setRecommendations] = useState([]);

  const [loading, setLoading] = useState(true);
  const [apiStatus, setApiStatus] = useState('connecting'); // connecting, online, offline
  const [errorMsg, setErrorMsg] = useState('');

  // Load States on mount
  useEffect(() => {
    getStates()
      .then(data => {
        setStates(data.filter(s => s && s.toString().toUpperCase() !== 'NAN'));
        setApiStatus('online');
      })
      .catch(err => {
        console.error("Failed to load states", err);
        setApiStatus('offline');
        setErrorMsg(err.message || 'Network Connection Refused');
      });
  }, []);

  // Load Districts when State changes
  useEffect(() => {
    if (selectedState) {
      getDistricts(selectedState).then(data => setDistricts(data.filter(d => d && d.toString().toUpperCase() !== 'NAN')));
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

  const clearFilters = () => {
    setSelectedState('');
    setSelectedDistrict('');
    setEnrolmentData([]);
    setDemographicData([]);
    setBiometricData([]);
    setRecommendations([]);
  };

  // Fetch all recommendations for the map on mount
  const [allRecommendations, setAllRecommendations] = useState([]);
  useEffect(() => {
    getRecommendations().then(setAllRecommendations);
  }, []);

  const today = new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });

  return (
    <div className="app-container">
      <header className="header">
        <div className="header-content">
          <h1>UIDAI Load Predictor</h1>
          <p className="subtitle">Advanced Infrastructure Scaling & Predictive Analytics Dashboard</p>
        </div>
        <div className="header-stats flex flex-col items-end">
          <div className="flex items-center gap-2 mb-1">
            <span className={`w-2 h-2 rounded-full ${apiStatus === 'online' ? 'bg-green-500 animate-pulse' : (apiStatus === 'offline' ? 'bg-red-500' : 'bg-amber-400')}`}></span>
            <span className={`text-xs font-bold uppercase tracking-tighter ${apiStatus === 'online' ? 'text-slate-500' : (apiStatus === 'offline' ? 'text-red-600' : 'text-amber-600')}`}>
              {apiStatus === 'online' ? 'Engine Online' : (apiStatus === 'offline' ? 'Engine Offline' : 'Connecting...')}
            </span>
          </div>
          {apiStatus === 'offline' ? (
            <span className="text-[10px] font-bold text-red-400 uppercase bg-red-50 px-2 py-0.5 rounded border border-red-100">
              {errorMsg}
            </span>
          ) : (
            <span className="text-sm font-medium text-slate-400">System Refreshed: {today}</span>
          )}
        </div>
      </header>

      <div className="top-grid-reorganized">
        <div className="dashboard-controls-section">
          <div className="section-header no-border mb-4">
            <h2>Strategic Region Selection</h2>
          </div>
          <div className="dashboard-controls-compact">
            <div className="filter-group">
              <label>State Scope</label>
              <select value={selectedState} onChange={(e) => setSelectedState(e.target.value)}>
                <option value="">Select State</option>
                {states.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>

            <div className="filter-group mt-4">
              <label>District Detail</label>
              <select value={selectedDistrict} onChange={(e) => setSelectedDistrict(e.target.value)} disabled={!selectedState}>
                <option value="">All Districts in {selectedState || '...'}</option>
                {districts.map(d => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>

          </div>
        </div>

        <section className="section recs-section-top">
          <div className="section-header">
            <h2>Machine Deployment & Infrastructure Roadmap</h2>
            <span className="badge badge-blue">{recommendations.length} Districts Analyzed</span>
          </div>
          <div className="recs-grid-compact">
            {selectedState && selectedDistrict && recommendations.length > 0 ? (
              recommendations.slice(0, 1).map((rec, idx) => (
                <RecommendationCard key={idx} recommendation={rec} />
              ))
            ) : (
              <div className="empty-state-compact">
                <div className="text-2xl mb-2">🗺️</div>
                {selectedState && !selectedDistrict
                  ? "Select a District to view infrastructure roadmap."
                  : "Select State and District to generate scaling plans."}
              </div>
            )}
          </div>
        </section>
      </div>

      <main className="dashboard-main-content">
        <section className="section charts-section-full">
          <div className="section-header">
            <h2>Predictive Load Trajectories</h2>
            <span className="location-tag">
              {selectedDistrict ? `Focus: ${selectedDistrict}` : (selectedState ? `Scope: ${selectedState}` : 'Pending Regional Input')}
            </span>
          </div>
          <div className="charts-container-horizontal">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <ForecastChart data={enrolmentData} type="enrolment" title="Enrolment Trend" />
              <ForecastChart data={demographicData} type="demographic" title="Demographic Drift" />
              <ForecastChart data={biometricData} type="biometric" title="Biometric Security" />
            </div>
          </div>
        </section>

        <div className="map-wrapper-full mt-4">
          <HighDemandMap recommendations={allRecommendations} />
        </div>
      </main>

      <footer className="footer">
        <div className="flex flex-col items-center gap-2">
          <div className="w-8 h-1 bg-slate-200 rounded-full mb-2"></div>
          <p>© 2026 UIDAI Load Predictor</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
