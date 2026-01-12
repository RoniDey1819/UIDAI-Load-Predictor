import React from 'react';
import Plot from 'react-plotly.js';

const ForecastChart = ({ data, type, title }) => {
    if (!data || data.length === 0) {
        return <div className="p-4 text-center text-gray-500">No data available for chart</div>;
    }

    // Sort by date
    const sortedData = [...data].sort((a, b) => new Date(a.month) - new Date(b.month));

    const dates = sortedData.map(d => d.month);
    const values = sortedData.map(d => d.forecast_value);

    // Dynamic color based on type
    const colorMap = {
        'enrolment': '#3b82f6', // blue
        'demographic': '#f59e0b', // amber
        'biometric': '#ef4444', // red
    };

    return (
        <div className="w-full h-full bg-white rounded-lg shadow p-4">
            <h3 className="text-lg font-bold mb-4">{title}</h3>
            <Plot
                data={[
                    {
                        x: dates,
                        y: values,
                        type: 'scatter',
                        mode: 'lines+markers',
                        marker: { color: colorMap[type] || '#8884d8' },
                        name: 'Forecast',
                    },
                ]}
                layout={{
                    autosize: true,
                    margin: { l: 50, r: 20, t: 20, b: 50 },
                    xaxis: { title: 'Date' },
                    yaxis: { title: 'Volume' },
                    showlegend: true,
                }}
                useResizeHandler={true}
                style={{ width: '100%', height: '400px' }}
            />
        </div>
    );
};

export default ForecastChart;
