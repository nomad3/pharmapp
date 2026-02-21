import React from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from "recharts";

function fmtCLP(v) {
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
  if (v >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
  return `$${v}`;
}

export default function SalesTrendChart({ data, title, isCenabast }) {
  if (!data || data.length === 0) return <div className="chart-empty">Sin datos de tendencia</div>;

  return (
    <div className="chart-container">
      <h3 className="chart-title">{title || "Tendencia de Ventas"}</h3>
      <ResponsiveContainer width="100%" height={350}>
        <LineChart data={data} margin={{ left: 10, right: 20, top: 10, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis dataKey="period" tick={{ fontSize: 11 }} angle={-45} textAnchor="end" height={60} />
          <YAxis tickFormatter={fmtCLP} tick={{ fontSize: 11 }} />
          <Tooltip formatter={(v) => `$${v.toLocaleString("es-CL")}`} />
          <Legend />
          {isCenabast ? (
            <Line type="monotone" dataKey="total_revenue" name="Revenue" stroke="#1565C0" strokeWidth={2} dot={false} />
          ) : (
            <>
              <Line type="monotone" dataKey="bms_revenue" name="BMS" stroke="#00695C" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="competition_revenue" name="Competencia" stroke="#E53935" strokeWidth={2} dot={false} />
            </>
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
