import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';

const Heatmap = ({ data, title, onDistrictSelect }) => {
    if (!data || data.length === 0) {
        return <div className="p-4 text-center text-gray-500">No data available for map</div>;
    }

    const { districts, months, zValues } = useMemo(() => {
        let filteredData = data;
        const allDistricts = [...new Set(data.map(d => d.district))];

        // Top-N logic for high-cardinality views
        if (allDistricts.length > 50) {
            const districtTotals = {};
            data.forEach(d => {
                districtTotals[d.district] = (districtTotals[d.district] || 0) + d.forecast_value;
            });

            const topDistricts = Object.entries(districtTotals)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 30)
                .map(([d]) => d);

            filteredData = data.filter(d => topDistricts.includes(d.district));
        }

        // Sort districts and months
        const uniqueDistricts = [...new Set(filteredData.map(d => d.district))].sort().reverse();
        const uniqueMonths = [...new Set(filteredData.map(d => d.month))].sort();

        // Build Z matrix (rows = districts, cols = months)
        const z = uniqueDistricts.map(() => uniqueMonths.map(() => 0));

        filteredData.forEach(d => {
            const rowIdx = uniqueDistricts.indexOf(d.district);
            const colIdx = uniqueMonths.indexOf(d.month);
            if (rowIdx >= 0 && colIdx >= 0) {
                z[rowIdx][colIdx] = d.forecast_value;
            }
        });

        return { districts: uniqueDistricts, months: uniqueMonths, zValues: z };
    }, [data]);

    const displayTitle = districts.length >= 30 ? `${title} (Top 30 Listed)` : title;

    return (
        <div className="heatmap-container">
            <div className="heatmap-header">
                <h3 className="heatmap-title">{displayTitle}</h3>
            </div>
            <Plot
                data={[
                    {
                        z: zValues,
                        x: months.map(m => m.split(' ')[0]),
                        y: districts,
                        type: 'heatmap',
                        colorscale: 'Viridis',
                        showscale: true,
                        hovertemplate: '<b>%{y}</b><br>Month: %{x}<br>Forecast: %{z:,.0f}<extra></extra>',
                    },
                ]}
                layout={{
                    autosize: true,
                    margin: { l: 150, r: 20, t: 10, b: 60 },
                    xaxis: {
                        title: 'Forecast Month',
                        tickangle: -30,
                        automargin: true,
                    },
                    yaxis: {
                        title: '',
                        automargin: true,
                    },
                    font: { family: 'Inter, sans-serif', size: 10 },
                    plot_bgcolor: '#f8fafc',
                    paper_bgcolor: '#ffffff',
                }}
                useResizeHandler={true}
                style={{ width: '100%', height: '500px' }}
                onClick={(ev) => {
                    if (ev.points && ev.points[0]) {
                        const district = ev.points[0].y;
                        if (onDistrictSelect) onDistrictSelect(district);
                    }
                }}
                config={{ displayModeBar: false }}
            />
            <div className="heatmap-footer">
                <span className="hint">💡 Click a specific district to load detailed analytics</span>
            </div>
        </div>
    );
};

export default Heatmap;
