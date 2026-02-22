import React from "react";

export default function RegionalHeatmap({ data }) {
  if (!data || data.length === 0) return null;

  const maxRevenue = Math.max(...data.map((d) => d.total_revenue), 1);

  return (
    <div className="regional-heatmap">
      {data.map((item) => {
        const intensity = Math.min(1, item.total_revenue / maxRevenue);
        const bgColor = `rgba(16, 185, 129, ${0.1 + intensity * 0.8})`;

        return (
          <div key={item.region} className="regional-heatmap__region" style={{ backgroundColor: bgColor }}>
            <div className="regional-heatmap__name">{item.region}</div>
            <div className="regional-heatmap__stats">
              <span>${Math.round(item.total_revenue).toLocaleString("es-CL")}</span>
              <span>{item.total_units?.toLocaleString("es-CL")} uds</span>
              {item.per_capita_units > 0 && (
                <span>{item.per_capita_units} per cap</span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
