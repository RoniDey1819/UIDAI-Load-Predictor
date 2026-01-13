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
        setStates(data);
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

      <div className="dashboard-controls">
        <div className="filter-group">
          <label>Strategic Region Selection</label>
          <div className="select-row">
            <select value={selectedState} onChange={(e) => setSelectedState(e.target.value)}>
              <option value="">Select State (National Overview)</option>
              {states.map(s => <option key={s} value={s}>{s}</option>)}
            </select>

            <select value={selectedDistrict} onChange={(e) => setSelectedDistrict(e.target.value)} disabled={!selectedState}>
              <option value="">All Districts in {selectedState || '...'}</option>
              {districts.map(d => <option key={d} value={d}>{d}</option>)}
            </select>

            <button onClick={clearFilters} className="btn-clear group">
              <span className="group-hover:rotate-180 transition-transform duration-500">🔄</span>
              Reset Perspective
            </button>
          </div>
        </div>
      </div>

      <main className="dashboard-grid">
        <div className="details-grid">
          <section className="section charts-section">
            <div className="section-header">
              <h2>Predictive Load Trajectories</h2>
              <span className="location-tag">
                {selectedDistrict ? `Focus: ${selectedDistrict}` : (selectedState ? `Scope: ${selectedState}` : 'Pending Regional Input')}
              </span>
            </div>
            <div className="charts-container">
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                <ForecastChart data={enrolmentData} type="enrolment" title="New Enrolment (Projected)" />
                <ForecastChart data={demographicData} type="demographic" title="Demographic Drift" />
              </div>
              <ForecastChart data={biometricData} type="biometric" title="Biometric Security Updates" />
            </div>
          </section>

          <section className="section recs-section">
            <div className="section-header">
              <h2>Machine Deployment & Infrastructure Roadmap</h2>
              <span className="badge badge-blue">{recommendations.length} Districts Analyzed</span>
            </div>
            <div className="recs-grid">
              {recommendations.slice(0, 8).map((rec, idx) => (
                <RecommendationCard key={idx} recommendation={rec} />
              ))}
              {recommendations.length === 0 && (
                <div className="empty-state">
                  <div className="text-4xl mb-4">🗺️</div>
                  Please select a State or District to generate behavioral-aware infrastructure scaling plans.
                </div>
              )}
            </div>
          </section>
        </div>

        <div className="map-wrapper mt-8">
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
