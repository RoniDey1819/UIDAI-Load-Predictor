import React from 'react';

const RecommendationCard = ({ recommendation }) => {
    // Determine style based on content
    const isHighPriority = recommendation.Recommendation.includes("High Demand") || recommendation.Recommendation.includes("Advanced");

    return (
        <div className={`card ${isHighPriority ? 'bg-red-50 border-l-4 border-red-500 shadow-md' : 'border-l-4 border-blue-500'}`}>
            <div className="card-body p-4">
                <div className="flex justify-between items-start mb-2">
                    <h4 className="font-bold text-gray-800">{recommendation.district}</h4>
                    <span className="text-[10px] bg-white px-2 py-0.5 rounded shadow-sm text-gray-500">{recommendation.state}</span>
                </div>

                <p className="text-sm font-medium text-blue-800 mb-3 leading-tight">{recommendation.Recommendation}</p>

                <div className="grid grid-cols-1 gap-2 border-t pt-2">
                    <div className="flex justify-between items-center text-[11px]">
                        <span className="text-gray-500">Category</span>
                        <span className="font-medium text-gray-400">Past 6m → Forecast 6m</span>
                    </div>

                    <div className="flex justify-between items-center text-xs">
                        <span className="text-gray-600 font-semibold">Enrolment:</span>
                        <span className="font-mono">{recommendation.prev_avg_enrolment} → <span className="text-blue-600 font-bold">{recommendation.avg_enrolment}</span></span>
                    </div>

                    <div className="flex justify-between items-center text-xs">
                        <span className="text-gray-600 font-semibold">Demographic:</span>
                        <span className="font-mono">{recommendation.prev_avg_demographic} → <span className="text-blue-600 font-bold">{recommendation.avg_demographic}</span></span>
                    </div>

                    <div className="flex justify-between items-center text-xs">
                        <span className="text-gray-600 font-semibold">Biometric:</span>
                        <span className="font-mono">{recommendation.prev_avg_biometric} → <span className="text-blue-600 font-bold">{recommendation.avg_biometric}</span></span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default RecommendationCard;
