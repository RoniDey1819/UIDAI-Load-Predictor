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
    const bioHighDistricts = recommendations.filter(rec => {
        const hasRec = rec.Recommendation && rec.Recommendation.includes("Advanced Biometric Infrastructure Recommended");
        const lat = parseFloat(rec.latitude);
        const lng = parseFloat(rec.longitude);
        const hasCoords = !isNaN(lat) && !isNaN(lng) && lat !== 0 && lng !== 0;
        return hasRec && hasCoords;
    });

    console.log(`[Map Debug] Input: ${recommendations.length} total, Filtered: ${bioHighDistricts.length} priority zones`);

    // Precise bounds for India to ensure Kashmir and all borders are visible
    const indiaBounds = [
        [6.746, 68.032], // Southwest
        [37.592, 97.412]  // Northeast
    ];

    return (
        <section className="section map-section">
            <div className="section-header">
                <h2>Strategic Biometric Expansion Map</h2>
                <span className="badge badge-red">{bioHighDistricts.length} Priority Zones</span>
            </div>

            <p className="text-sm text-slate-500 mb-4">
                Visualizing districts exceeding the <strong>15,000 monthly activity threshold</strong> requiring immediate Advanced Biometric infrastructure expansion.
            </p>

            <div className="map-container overflow-hidden rounded-xl border border-slate-200">
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
                                <div className="p-1">
                                    <div className="bg-slate-900 text-white p-3 rounded-t-lg -m-1 mb-2">
                                        <div className="font-bold text-sm tracking-tight">{d.district}</div>
                                        <div className="text-[10px] text-slate-400 font-bold uppercase">{d.state}</div>
                                    </div>
                                    <div className="p-1 space-y-2">
                                        <div className="flex justify-between items-center text-xs">
                                            <span className="text-slate-500">Predicted Load:</span>
                                            <span className="font-bold text-blue-600">{d.avg_biometric.toLocaleString()}</span>
                                        </div>
                                        <div className="flex justify-between items-center text-xs">
                                            <span className="text-slate-500">Growth Intensity:</span>
                                            <span className="font-bold text-green-600">
                                                +{d.prev_avg_biometric > 0
                                                    ? ((d.avg_biometric - d.prev_avg_biometric) / d.prev_avg_biometric * 100).toFixed(1)
                                                    : '0.0'}%
                                            </span>
                                        </div>
                                        <div className="pt-2 border-t mt-2 text-[9px] text-slate-400 text-center font-mono">
                                            COORD: {d.latitude.toFixed(3)}, {d.longitude.toFixed(3)}
                                        </div>
                                    </div>
                                </div>
                            </Popup>
                        </Marker>
                    ))}
                </MapContainer>
            </div>
        </section>
    );
};

export default HighDemandMap;
