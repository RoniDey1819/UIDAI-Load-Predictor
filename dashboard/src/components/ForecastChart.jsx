import React from 'react';
import Plot from 'react-plotly.js';

const ForecastChart = ({ data, type, title }) => {
    if (!data || data.length === 0) {
        return <div className="p-4 text-center text-gray-500">No data available for chart</div>;
    }

    // Sort by date
    const sortedData = [...data].sort((a, b) => new Date(a.month) - new Date(b.month));

    const historicalData = sortedData.filter(d => !d.is_forecast);
    const forecastData = sortedData.filter(d => d.is_forecast);

    // Dynamic color based on type
    const colorMap = {
        'enrolment': '#3b82f6', // blue
        'demographic': '#f59e0b', // amber
        'biometric': '#ef4444', // red
    };

    const baseColor = colorMap[type] || '#8884d8';

    return (
        <div className="forecast-chart-card">
            <h3 className="chart-title">{title}</h3>
            <Plot
                data={[
                    {
                        x: historicalData.map(d => d.month),
                        y: historicalData.map(d => d.value),
                        type: 'scatter',
                        mode: 'lines+markers',
                        marker: { color: baseColor, opacity: 0.6 },
                        line: { color: baseColor, width: 2, dash: 'dot' },
                        name: 'History (6m)',
                    },
                    {
                        x: forecastData.map(d => d.month),
                        y: forecastData.map(d => d.value),
                        type: 'scatter',
                        mode: 'lines+markers',
                        marker: { color: baseColor, size: 8 },
                        line: { color: baseColor, width: 4 },
                        name: 'Forecast Spike',
                    },
                ]}
                layout={{
                    autosize: true,
                    margin: { l: 50, r: 20, t: 30, b: 50 },
                    xaxis: { title: 'Timeline' },
                    yaxis: { title: 'Demand Volume' },
                    showlegend: true,
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                }}
                useResizeHandler={true}
                style={{ width: '100%', height: '350px' }}
            />
        </div>
    );
};

export default ForecastChart;
