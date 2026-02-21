import React, { useState } from "react";

function fmtCLP(v) {
  return `$${Math.round(v).toLocaleString("es-CL")}`;
}

export default function TopInstitutionsTable({ data, title, columns }) {
  const [sortKey, setSortKey] = useState("total_revenue");
  const [sortAsc, setSortAsc] = useState(false);

  if (!data || data.length === 0) return <div className="chart-empty">Sin datos de instituciones</div>;

  const cols = columns || [
    { key: "razon_social", label: "Institución", fmt: (v) => v || "—" },
    { key: "region", label: "Región", fmt: (v) => v || "—" },
    { key: "total_units", label: "Unidades", fmt: (v) => (v || 0).toLocaleString("es-CL") },
    { key: "total_revenue", label: "Revenue", fmt: fmtCLP },
  ];

  const sorted = [...data].sort((a, b) => {
    const av = a[sortKey] ?? 0;
    const bv = b[sortKey] ?? 0;
    return sortAsc ? (av > bv ? 1 : -1) : (av < bv ? 1 : -1);
  });

  function handleSort(key) {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(false); }
  }

  return (
    <div className="chart-container">
      <h3 className="chart-title">{title || "Top Instituciones"}</h3>
      <div className="table-scroll">
        <table className="analytics-table">
          <thead>
            <tr>
              <th>#</th>
              {cols.map((c) => (
                <th key={c.key} onClick={() => handleSort(c.key)} style={{ cursor: "pointer" }}>
                  {c.label} {sortKey === c.key ? (sortAsc ? "↑" : "↓") : ""}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((row, i) => (
              <tr key={i}>
                <td>{i + 1}</td>
                {cols.map((c) => (
                  <td key={c.key}>{c.fmt(row[c.key])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
