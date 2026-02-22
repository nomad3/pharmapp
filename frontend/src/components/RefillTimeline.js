import React from "react";

const STATUS_CONFIG = {
  on_time: { color: "#10b981", label: "A tiempo" },
  late: { color: "#f59e0b", label: "Tarde" },
  missed: { color: "#ef4444", label: "No recogido" },
  pending: { color: "#6b7280", label: "Pendiente" },
};

export default function RefillTimeline({ refills }) {
  if (!refills || refills.length === 0) {
    return <p className="empty-state">No hay refills registrados.</p>;
  }

  return (
    <div className="refill-timeline">
      {refills.map((refill) => {
        const config = STATUS_CONFIG[refill.status] || STATUS_CONFIG.pending;
        const dueDate = new Date(refill.due_date).toLocaleDateString("es-CL");
        const actualDate = refill.actual_date ? new Date(refill.actual_date).toLocaleDateString("es-CL") : null;

        return (
          <div key={refill.id} className="refill-timeline__item">
            <div className="refill-timeline__dot" style={{ backgroundColor: config.color }} />
            <div className="refill-timeline__content">
              <div className="refill-timeline__header">
                <span className="refill-timeline__status" style={{ color: config.color }}>
                  {config.label}
                </span>
                <span className="refill-timeline__date">Vence: {dueDate}</span>
              </div>
              {actualDate && (
                <div className="refill-timeline__actual">Recogido: {actualDate}</div>
              )}
              {refill.discount_amount > 0 && (
                <div className="refill-timeline__discount">
                  Descuento: ${Math.round(refill.discount_amount).toLocaleString("es-CL")} ({Math.round(refill.discount_pct_applied * 100)}%)
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
