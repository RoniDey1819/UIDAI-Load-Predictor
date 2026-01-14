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
        <div className={`card ${isHighPriority ? 'border-t-4 border-red-500 shadow-md' : 'border-t-2 border-slate-200'}`}>
            <div className="card-header pb-2 px-3 pt-3">
                <div className="flex flex-col">
                    <h4 className="font-extrabold text-slate-900 m-0 tracking-tight text-sm leading-tight">{recommendation.district}</h4>
                    <span className="text-[9px] text-slate-400 font-bold uppercase tracking-widest">{recommendation.state}</span>
                </div>
                <span className={`badge ${getBadgeStyle(baseRec)} shadow-sm text-[9px] px-2 py-0.5`}>
                    {baseRec}
                </span>
            </div>

            <div className="card-body px-3 pb-3 pt-1">
                {hasBiometric && (
                    <div className="mb-2 p-2 bg-blue-50 rounded-md border border-blue-100 flex items-center gap-2">
                        <span className="text-sm">🛡️</span>
                        <span className="text-[9px] font-extrabold text-blue-700 leading-tight uppercase tracking-tight">
                            Advanced Biometric Required
                        </span>
                    </div>
                )}

                <div className="metrics-grid" style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                    <div className="metrics-header" style={{
                        display: 'grid',
                        gridTemplateColumns: '80px 1fr 1fr',
                        gap: '8px',
                        padding: '6px 10px',
                        background: '#f8fafc',
                        borderRadius: '4px',
                        borderBottom: '1px solid #e2e8f0',
                        marginBottom: '8px'
                    }}>
                        <span style={{ fontSize: '8px', fontWeight: '900', color: '#64748b', letterSpacing: '0.05em' }}>SERVICE</span>
                        <span style={{ fontSize: '8px', fontWeight: '900', color: '#64748b', letterSpacing: '0.05em', textAlign: 'center' }}>PAST AVG</span>
                        <span style={{ fontSize: '8px', fontWeight: '900', color: '#64748b', letterSpacing: '0.05em', textAlign: 'right' }}>FUTURE PEAK</span>
                    </div>

                    {[
                        { label: 'Enrolment', current: recommendation.prev_avg_enrolment, forecast: recommendation.avg_enrolment },
                        { label: 'Demographic', current: recommendation.prev_avg_demographic, forecast: recommendation.avg_demographic },
                        { label: 'Biometric', current: recommendation.prev_avg_biometric, forecast: recommendation.avg_biometric },
                    ].map((item, idx) => (
                        <div key={idx} className="metric-row" style={{
                            display: 'grid',
                            gridTemplateColumns: '80px 1fr 1fr',
                            gap: '8px',
                            alignItems: 'center',
                            padding: '4px 10px',
                            marginBottom: '2px'
                        }}>
                            <span style={{ fontSize: '11px', fontWeight: '700', color: '#1e293b' }}>{item.label}</span>
                            <span style={{ fontSize: '11px', fontFamily: 'monospace', color: '#94a3b8', textAlign: 'center' }}>{formatNum(item.current)}</span>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '6px' }}>
                                <span style={{ fontSize: '9px', color: item.forecast > item.current ? '#ef4444' : '#22c55e', fontWeight: 'bold' }}>
                                    {item.forecast > item.current ? '▲' : '▼'}
                                </span>
                                <span style={{ fontSize: '12px', fontWeight: '900', fontFamily: 'monospace', color: 'var(--primary)' }}>{formatNum(item.forecast)}</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default RecommendationCard;
