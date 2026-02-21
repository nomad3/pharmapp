import React from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

function fmtCLP(v) {
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
  if (v >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
  return `$${v}`;
}

export default function RegionChart({ data, title, color }) {
  if (!data || data.length === 0) return <div className="chart-empty">Sin datos regionales</div>;

  const chartData = data.map((d) => ({
    name: d.region && d.region.length > 20 ? d.region.slice(0, 20) + "..." : d.region,
    revenue: d.total_revenue,
    units: d.total_units,
  }));

  return (
    <div className="chart-container">
      <h3 className="chart-title">{title || "Distribución Regional"}</h3>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={chartData} layout="vertical" margin={{ left: 20, right: 20, top: 10, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis type="number" tickFormatter={fmtCLP} />
          <YAxis type="category" dataKey="name" width={150} tick={{ fontSize: 11 }} />
          <Tooltip formatter={(v) => `$${v.toLocaleString("es-CL")}`} />
          <Bar dataKey="revenue" name="Revenue" fill={color || "#1565C0"} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
