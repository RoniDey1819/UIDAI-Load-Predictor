import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';

const Heatmap = ({ data, title, onDistrictSelect }) => {
    if (!data || data.length === 0) {
        return <div className="p-4 text-center text-slate-500 font-medium italic">No data available for analytical mapping</div>;
    }

    const { districts, months, zValues } = useMemo(() => {
        let filteredData = data;
        const allDistricts = [...new Set(data.map(d => d.district))];

        // Top-30 logic for clarity
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

        const uniqueDistricts = [...new Set(filteredData.map(d => d.district))].sort().reverse();
        const uniqueMonths = [...new Set(filteredData.map(d => d.month))].sort();

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

    const displayTitle = districts.length >= 30 ? `${title} (Critical Top 30)` : title;

    return (
        <div className="section mt-8">
            <div className="section-header">
                <h2>{displayTitle}</h2>
                <span className="badge badge-amber">Heatmap Analysis</span>
            </div>

            <Plot
                data={[
                    {
                        z: zValues,
                        x: months.map(m => m.split(' ')[0]),
                        y: districts,
                        type: 'heatmap',
                        colorscale: 'Blues',
                        showscale: true,
                        hovertemplate: '<b>%{y}</b><br>Month: %{x}<br>Forecast Load: %{z:,.0f}<extra></extra>',
                    },
                ]}
                layout={{
                    autosize: true,
                    margin: { l: 150, r: 20, t: 10, b: 60 },
                    xaxis: {
                        title: 'Timeline Projections',
                        tickangle: -30,
                        automargin: true,
                        gridcolor: '#f8fafc'
                    },
                    yaxis: {
                        automargin: true,
                    },
                    font: { family: 'Source Sans 3', size: 11 },
                    plot_bgcolor: '#f8fafc',
                    paper_bgcolor: 'rgba(0,0,0,0)',
                }}
                useResizeHandler={true}
                style={{ width: '100%', height: '550px' }}
                onClick={(ev) => {
                    if (ev.points && ev.points[0]) {
                        const district = ev.points[0].y;
                        if (onDistrictSelect) onDistrictSelect(district);
                    }
                }}
                config={{ displayModeBar: false, responsive: true }}
            />
            <div className="mt-4 p-3 bg-slate-50 rounded-lg text-slate-500 text-xs flex items-center gap-2">
                <span className="text-lg">💡</span>
                <span>Select a specific region on the matrix above to view localized demand trajectories.</span>
            </div>
        </div>
    );
};

export default Heatmap;
