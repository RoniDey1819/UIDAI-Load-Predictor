import React from 'react';

const RecommendationCard = ({ recommendation }) => {
    const recText = recommendation.Recommendation || "";
    const hasBiometric = recText.includes("Advanced Biometric");

    // Clean label (remove the biometric part)
    const baseRec = recText.split(" + ")[0];

    // Determine priority and style
    const getBadgeStyle = (text) => {
        if (text.includes("High")) return "badge-red";
        if (text.includes("Average")) return "badge-amber";
        if (text.includes("Enrolment-Centric")) return "badge-green";
        if (text.includes("Update-Only")) return "badge-blue";
        return "badge-blue text-gray-500 bg-gray-100";
    };

    const isHighPriority = recText.includes("High Activities");

    const formatNum = (val) => Math.round(parseFloat(val) || 0).toLocaleString();

    return (
        <div className={`card ${isHighPriority ? 'border-t-4 border-red-500 shadow-lg' : 'border-t-2 border-slate-200'}`}>
            <div className="card-header pb-4">
                <div className="flex flex-col">
                    <h4 className="font-extrabold text-slate-900 m-0 tracking-tight">{recommendation.district}</h4>
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">{recommendation.state}</span>
                </div>
                <span className={`badge ${getBadgeStyle(baseRec)} shadow-sm`}>
                    {baseRec}
                </span>
            </div>

            <div className="card-body pt-2">
                {hasBiometric && (
                    <div className="mb-4 p-2.5 bg-blue-50 rounded-lg border border-blue-100 flex items-center gap-3">
                        <span className="text-base">🛡️</span>
                        <span className="text-[10px] font-extrabold text-blue-700 leading-tight uppercase tracking-tight">
                            Advanced Biometric Infrastructure Required
                        </span>
                    </div>
                )}

                <div className="metrics-grid" style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div className="metrics-header" style={{
                        display: 'grid',
                        gridTemplateColumns: '100px 1fr 1fr',
                        gap: '12px',
                        padding: '10px 12px',
                        background: '#f8fafc',
                        borderRadius: '6px',
                        borderBottom: '1px solid #e2e8f0',
                        marginBottom: '12px'
                    }}>
                        <span style={{ fontSize: '9px', fontWeight: '900', color: '#64748b', letterSpacing: '0.05em' }}>SERVICE</span>
                        <span style={{ fontSize: '9px', fontWeight: '900', color: '#64748b', letterSpacing: '0.05em', textAlign: 'center' }}>PAST LOAD (AVG)</span>
                        <span style={{ fontSize: '9px', fontWeight: '900', color: '#64748b', letterSpacing: '0.05em', textAlign: 'right' }}>FUTURE PEAK (EXP)</span>
                    </div>

                    {[
                        { label: 'Enrolment', current: recommendation.prev_avg_enrolment, forecast: recommendation.avg_enrolment },
                        { label: 'Demographic', current: recommendation.prev_avg_demographic, forecast: recommendation.avg_demographic },
                        { label: 'Biometric', current: recommendation.prev_avg_biometric, forecast: recommendation.avg_biometric },
                    ].map((item, idx) => (
                        <div key={idx} className="metric-row" style={{
                            display: 'grid',
                            gridTemplateColumns: '100px 1fr 1fr',
                            gap: '12px',
                            alignItems: 'center',
                            padding: '6px 12px',
                            marginBottom: '4px'
                        }}>
                            <span style={{ fontSize: '12px', fontWeight: '700', color: '#1e293b' }}>{item.label}</span>
                            <span style={{ fontSize: '13px', fontFamily: 'monospace', color: '#94a3b8', textAlign: 'center' }}>{formatNum(item.current)}</span>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '8px' }}>
                                <span style={{ fontSize: '10px', color: item.forecast > item.current ? '#ef4444' : '#22c55e', fontWeight: 'bold' }}>
                                    {item.forecast > item.current ? '▲' : '▼'}
                                </span>
                                <span style={{ fontSize: '14px', fontWeight: '900', fontFamily: 'monospace', color: 'var(--primary)' }}>{formatNum(item.forecast)}</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default RecommendationCard;
