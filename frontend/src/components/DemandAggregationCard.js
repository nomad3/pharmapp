import React from "react";

export default function DemandAggregationCard({ item }) {
  const progressPct = Math.min(100, (item.total_quantity / item.threshold) * 100);
  const isReady = item.threshold_met;

  return (
    <div className={`demand-card ${isReady ? "demand-card--ready" : ""}`}>
      <div className="demand-card__header">
        <h3 className="demand-card__title">{item.product_name}</h3>
        {isReady && <span className="demand-card__badge">Listo para orden</span>}
      </div>
      <div className="demand-card__stats">
        <span>{item.total_quantity.toLocaleString("es-CL")} unidades</span>
        <span>{item.member_count} miembros</span>
      </div>
      <div className="demand-card__progress">
        <div className="demand-card__progress-bar">
          <div
            className="demand-card__progress-fill"
            style={{ width: `${progressPct}%` }}
          />
        </div>
        <span className="demand-card__progress-text">
          {Math.round(progressPct)}% del mínimo ({item.threshold})
        </span>
      </div>
    </div>
  );
}
