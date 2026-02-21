import React from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from "recharts";

export default function MarketShareChart({ data }) {
  if (!data || data.length === 0) return <div className="chart-empty">Sin datos de market share</div>;

  const chartData = data.slice(0, 15).map((d) => ({
    name: d.drug && d.drug.length > 18 ? d.drug.slice(0, 18) + "..." : d.drug,
    BMS: d.bms_units,
    Competencia: d.competition_units,
    share: d.bms_share_pct,
  }));

  return (
    <div className="chart-container">
      <h3 className="chart-title">Market Share BMS vs Competencia (unidades)</h3>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={chartData} layout="vertical" margin={{ left: 20, right: 20, top: 10, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis type="number" tickFormatter={(v) => v.toLocaleString("es-CL")} />
          <YAxis type="category" dataKey="name" width={140} tick={{ fontSize: 12 }} />
          <Tooltip formatter={(v) => v.toLocaleString("es-CL")} />
          <Legend />
          <Bar dataKey="BMS" fill="#00695C" />
          <Bar dataKey="Competencia" fill="#E53935" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
