import React from "react";

function fmt(n) {
  if (n >= 1e9) return `$${(n / 1e9).toFixed(1)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(1)}M`;
  if (n >= 1e3) return `$${(n / 1e3).toFixed(0)}K`;
  return n.toLocaleString("es-CL");
}

export default function SummaryCards({ data }) {
  if (!data) return null;
  const cards = [
    { label: "Registros BMS", value: (data.bms_distribution_records || 0).toLocaleString("es-CL"), color: "#00695C" },
    { label: "Facturas Cenabast", value: (data.cenabast_invoices || 0).toLocaleString("es-CL"), color: "#1565C0" },
    { label: "Revenue BMS", value: fmt(data.bms_total_revenue || 0), color: "#00695C" },
    { label: "Revenue Cenabast", value: fmt(data.cenabast_total_revenue || 0), color: "#1565C0" },
    { label: "Instituciones BMS", value: (data.bms_institutions || 0).toLocaleString("es-CL"), color: "#6A1B9A" },
    { label: "Productos Cenabast", value: (data.cenabast_products || 0).toLocaleString("es-CL"), color: "#E65100" },
    { label: "Medicamentos", value: (data.total_drugs || 0).toLocaleString("es-CL"), color: "#2E7D32" },
    { label: "OC + Adjudicaciones", value: ((data.bms_purchase_orders || 0) + (data.bms_adjudications || 0)).toLocaleString("es-CL"), color: "#AD1457" },
  ];

  return (
    <div className="summary-cards">
      {cards.map((c, i) => (
        <div key={i} className="summary-card">
          <div className="summary-card-value" style={{ color: c.color }}>{c.value}</div>
          <div className="summary-card-label">{c.label}</div>
        </div>
      ))}
    </div>
  );
}
