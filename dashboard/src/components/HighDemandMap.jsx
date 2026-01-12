import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default marker icons in React Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const HighDemandMap = ({ recommendations }) => {
    // Filter for districts that need advanced biometric kits
    const bioHighDistricts = recommendations.filter(rec =>
        rec.Recommendation.includes("Advanced Biometric Required") &&
        rec.latitude !== 0 &&
        rec.longitude !== 0
    );

    // Precise bounds for India to ensure Kashmir and all borders are visible
    const indiaBounds = [
        [6.746, 68.032], // Southwest
        [37.592, 97.412]  // Northeast
    ];

    return (
        <div className="section">
            <div className="section-header">
                <h2>Advanced Biometric High-Demand Zones</h2>
                <span>Districts requiring prioritized Advanced Biometric Kit deployment based on forecast growth</span>
            </div>

            <div className="map-container shadow-inner">
                <MapContainer
                    bounds={indiaBounds}
                    maxBounds={indiaBounds}
                    minZoom={4}
                    style={{ height: '100%', width: '100%' }}
                    scrollWheelZoom={false}
                >
                    <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                    {bioHighDistricts.map((d, idx) => (
                        <Marker key={idx} position={[d.latitude, d.longitude]}>
                            <Popup className="map-popup">
                                <div className="popup-header">
                                    {d.district}
                                </div>
                                <div className="popup-body">
                                    <div className="text-xs font-bold text-gray-400 mb-2 uppercase">{d.state}</div>
                                    <div className="popup-stat">
                                        <span className="popup-label">Monthly Bio Volume:</span>
                                        <span className="popup-value">{d.avg_biometric}</span>
                                    </div>
                                    <div className="popup-stat">
                                        <span className="popup-label">Forecast Growth:</span>
                                        <span className="popup-value text-green-600">
                                            {((d.avg_biometric - d.prev_avg_biometric) / d.prev_avg_biometric * 100).toFixed(1)}%
                                        </span>
                                    </div>
                                    <hr className="my-2" />
                                    <div className="text-[10px] text-gray-500 italic">
                                        Lat: {d.latitude.toFixed(4)}, Long: {d.longitude.toFixed(4)}
                                    </div>
                                </div>
                            </Popup>
                        </Marker>
                    ))}
                </MapContainer>
            </div>
        </div>
    );
};

export default HighDemandMap;
