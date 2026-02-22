import React from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

export default function PriceHistoryChart({ data, title }) {
  if (!data || data.length === 0) {
    return (
      <div className="chart-card">
        <h3>{title || "Historial de precios"}</h3>
        <p className="empty-chart">Sin datos de historial</p>
      </div>
    );
  }

  // Group by chain for multi-line chart
  const chains = [...new Set(data.map((d) => d.pharmacy_chain).filter(Boolean))];
  const colors = ["#00695C", "#1565C0", "#E65100", "#6A1B9A", "#2E7D32"];

  // Pivot data by date
  const dateMap = {};
  data.forEach((d) => {
    if (!dateMap[d.date]) dateMap[d.date] = { date: d.date };
    if (d.pharmacy_chain) {
      dateMap[d.date][d.pharmacy_chain] = d.price;
    }
  });
  const chartData = Object.values(dateMap).sort((a, b) => a.date.localeCompare(b.date));

  return (
    <div className="chart-card">
      <h3>{title || "Historial de precios"}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} />
          <YAxis tickFormatter={(v) => `$${v.toLocaleString("es-CL")}`} />
          <Tooltip formatter={(v) => `$${Math.round(v).toLocaleString("es-CL")}`} />
          <Legend />
          {chains.map((chain, i) => (
            <Line
              key={chain}
              type="monotone"
              dataKey={chain}
              stroke={colors[i % colors.length]}
              dot={false}
              strokeWidth={2}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
