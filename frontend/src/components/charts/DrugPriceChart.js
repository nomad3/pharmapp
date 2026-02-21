import React from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from "recharts";

function fmtCLP(v) {
  if (v >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
  if (v >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
  return `$${v}`;
}

export default function DrugPriceChart({ data }) {
  if (!data || data.length === 0) return <div className="chart-empty">Sin datos de precios</div>;

  const chartData = data.slice(0, 15).map((d) => ({
    name: d.drug && d.drug.length > 16 ? d.drug.slice(0, 16) + "..." : d.drug,
    "Precio BMS": d.avg_price_bms,
    "Precio Competencia": d.avg_price_competition,
  }));

  return (
    <div className="chart-container">
      <h3 className="chart-title">Comparación de Precios por Droga</h3>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={chartData} layout="vertical" margin={{ left: 20, right: 20, top: 10, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis type="number" tickFormatter={fmtCLP} />
          <YAxis type="category" dataKey="name" width={130} tick={{ fontSize: 12 }} />
          <Tooltip formatter={(v) => v ? `$${v.toLocaleString("es-CL")}` : "N/A"} />
          <Legend />
          <Bar dataKey="Precio BMS" fill="#00695C" />
          <Bar dataKey="Precio Competencia" fill="#E53935" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
