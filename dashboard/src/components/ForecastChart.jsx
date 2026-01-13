import React from 'react';
import Plot from 'react-plotly.js';

const ForecastChart = ({ data, type, title }) => {
    if (!data || data.length === 0) {
        return <div className="p-4 text-center text-gray-500 font-medium">No data available for chart</div>;
    }

    // Sort by date
    const sortedData = [...data].sort((a, b) => new Date(a.month) - new Date(b.month));

    const historicalData = sortedData.filter(d => !d.is_forecast);
    const forecastData = sortedData.filter(d => d.is_forecast);

    // Precise HSL Colors from design system
    const colorMap = {
        'enrolment': 'hsl(221, 83%, 53%)',
        'demographic': 'hsl(38, 92%, 50%)',
        'biometric': 'hsl(0, 84%, 60%)',
    };

    const baseColor = colorMap[type] || 'hsl(221, 83%, 53%)';

    return (
        <div className="forecast-chart-card">
            <h3 className="chart-title">
                <span className={`w-3 h-3 rounded-full`} style={{ backgroundColor: baseColor }}></span>
                {title}
            </h3>
            <Plot
                data={[
                    {
                        x: historicalData.map(d => d.month),
                        y: historicalData.map(d => d.value),
                        type: 'scatter',
                        mode: 'lines+markers',
                        marker: { color: baseColor, size: 6, opacity: 0.7 },
                        line: { color: baseColor, width: 2.5, shape: 'spline', smoothing: 1.3 },
                        name: 'Historical Trend',
                        hovertemplate: '<b>History</b>: %{y:,.0f}<br>Month: %{x}<extra></extra>',
                    },
                    {
                        x: forecastData.map(d => d.month),
                        y: forecastData.map(d => d.value),
                        type: 'scatter',
                        mode: 'lines+markers',
                        marker: { color: baseColor, size: 8, symbol: 'diamond' },
                        line: { color: baseColor, width: 4, shape: 'spline', dash: 'dash' },
                        name: 'Predicted Trend',
                        hovertemplate: '<b>Predicted</b>: %{y:,.0f}<br>Month: %{x}<extra></extra>',
                    },
                ]}
                layout={{
                    autosize: true,
                    margin: { l: 50, r: 20, t: 10, b: 100 },
                    font: { family: 'Source Sans 3', size: 12 },
                    xaxis: {
                        title: 'Timeline',
                        gridcolor: '#f1f5f9',
                        linecolor: '#e2e8f0',
                        rangeselector: {
                            buttons: [
                                { count: 3, label: '3m', step: 'month', stepmode: 'backward' },
                                { count: 6, label: '6m', step: 'month', stepmode: 'backward' },
                                { step: 'all', label: 'All' }
                            ]
                        }
                    },
                    yaxis: {
                        title: 'Volume',
                        gridcolor: '#f1f5f9',
                        linecolor: '#e2e8f0',
                        zerolinecolor: '#e2e8f0'
                    },
                    legend: {
                        orientation: 'h',
                        y: -0.45,
                        x: 0.5,
                        xanchor: 'center',
                        font: { size: 12 },
                        itemspacing: 40,
                        entrywidth: 200,
                        entrywidthmode: 'pixels'
                    },
                    hovermode: 'closest',
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                }}
                config={{ displayModeBar: false, responsive: true }}
                useResizeHandler={true}
                style={{ width: '100%', height: '340px' }}
            />
        </div>
    );
};

export default ForecastChart;
