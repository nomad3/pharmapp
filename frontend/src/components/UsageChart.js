import React from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export default function UsageChart({ data, title }) {
  if (!data || data.length === 0) {
    return (
      <div className="chart-card">
        <h3>{title || "API Usage"}</h3>
        <p className="empty-chart">Sin datos de uso</p>
      </div>
    );
  }

  return (
    <div className="chart-card">
      <h3>{title || "API Usage"}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="endpoint" tick={{ fontSize: 11 }} />
          <YAxis />
          <Tooltip />
          <Bar dataKey="count" fill="#00695C" name="Requests" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
