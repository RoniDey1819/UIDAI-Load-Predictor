import React from 'react';

const RecommendationCard = ({ recommendation }) => {
    // Determine style based on content
    const isHighPriority = recommendation.Recommendation.includes("Full-Service") || recommendation.Recommendation.includes("Advanced");

    return (
        <div className={`card ${isHighPriority ? 'border-l-4 border-red-500' : 'border-l-4 border-blue-500'}`}>
            <div className="card-body">
                <h4 className="font-bold">{recommendation.district}, {recommendation.state}</h4>
                <p className="text-sm mt-1">{recommendation.Recommendation}</p>
                <div className="flex gap-2 mt-2 text-xs text-gray-600">
                    <span>Enrol: {recommendation.avg_enrolment}</span>
                    <span>Demo: {recommendation.avg_demographic}</span>
                    <span>Bio: {recommendation.avg_biometric}</span>
                </div>
            </div>
        </div>
    );
};

export default RecommendationCard;
