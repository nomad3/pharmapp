import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import client from "../api/client";
import GpoSidebar from "../components/GpoSidebar";

const STATUS_STEPS = [
  "intent_collection",
  "aggregated",
  "submitted_to_cenabast",
  "confirmed",
  "fulfilled",
  "distributed",
];

const STATUS_LABELS = {
  intent_collection: "Recopilación",
  aggregated: "Agregado",
  submitted_to_cenabast: "Enviado a Cenabast",
  confirmed: "Confirmado",
  fulfilled: "Cumplido",
  distributed: "Distribuido",
};

export default function GpoGroupOrderPage() {
  const { slug, orderId } = useParams();
  const [order, setOrder] = useState(null);
  const [allocations, setAllocations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [orderRes, allocRes] = await Promise.all([
          client.get(`/gpo/groups/${slug}/orders/${orderId}`),
          client.get(`/gpo/groups/${slug}/orders/${orderId}/allocations`),
        ]);
        setOrder(orderRes.data);
        setAllocations(allocRes.data);
      } catch (err) {
        console.error("Error loading order:", err);
      }
      setLoading(false);
    };
    fetchData();
  }, [slug, orderId]);

  const handleStatusUpdate = async (newStatus) => {
    try {
      const { data } = await client.put(`/gpo/groups/${slug}/orders/${orderId}/status`, { status: newStatus });
      setOrder(data);
    } catch (err) {
      console.error("Error updating status:", err);
    }
  };

  if (loading) {
    return <div className="loading-state"><div className="spinner"></div></div>;
  }

  if (!order) {
    return <div className="container"><p>Orden no encontrada.</p></div>;
  }

  const currentStepIndex = STATUS_STEPS.indexOf(order.status);

  return (
    <div className="org-layout container">
      <GpoSidebar slug={slug} />
      <div className="org-main">
        <h1>Orden: {order.product_name}</h1>
        <p className="subtitle">Mes: {order.target_month}</p>

        <div className="order-lifecycle">
          {STATUS_STEPS.map((step, i) => (
            <div key={step} className={`lifecycle-step ${i <= currentStepIndex ? "lifecycle-step--completed" : ""} ${i === currentStepIndex ? "lifecycle-step--current" : ""}`}>
              <div className="lifecycle-step__dot" />
              <div className="lifecycle-step__label">{STATUS_LABELS[step]}</div>
            </div>
          ))}
        </div>

        <div className="transparency-stats-grid" style={{ marginTop: "2rem" }}>
          <div className="summary-card">
            <div className="summary-card__value">{order.total_quantity?.toLocaleString("es-CL")}</div>
            <div className="summary-card__label">Unidades totales</div>
          </div>
          <div className="summary-card">
            <div className="summary-card__value">{order.member_count}</div>
            <div className="summary-card__label">Miembros</div>
          </div>
          <div className="summary-card">
            <div className="summary-card__value">${order.unit_price_group?.toLocaleString("es-CL") || "—"}</div>
            <div className="summary-card__label">Precio unitario grupo</div>
          </div>
          <div className="summary-card">
            <div className="summary-card__value">${order.facilitation_fee?.toLocaleString("es-CL") || "—"}</div>
            <div className="summary-card__label">Fee facilitación</div>
          </div>
        </div>

        {currentStepIndex < STATUS_STEPS.length - 1 && (
          <div className="order-actions" style={{ marginTop: "1.5rem" }}>
            <button
              className="btn btn--primary"
              onClick={() => handleStatusUpdate(STATUS_STEPS[currentStepIndex + 1])}
            >
              Avanzar a: {STATUS_LABELS[STATUS_STEPS[currentStepIndex + 1]]}
            </button>
          </div>
        )}

        <section className="gpo-section" style={{ marginTop: "2rem" }}>
          <h2>Asignaciones por Miembro</h2>
          {allocations.length === 0 ? (
            <p className="empty-state">No hay asignaciones.</p>
          ) : (
            <div className="data-table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Miembro</th>
                    <th>Cantidad</th>
                    <th>Precio Unit.</th>
                    <th>Subtotal</th>
                    <th>Fee</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {allocations.map((alloc) => (
                    <tr key={alloc.id}>
                      <td>{alloc.gpo_member_id.slice(0, 8)}</td>
                      <td>{alloc.quantity_allocated?.toLocaleString("es-CL")}</td>
                      <td>${alloc.unit_price?.toLocaleString("es-CL")}</td>
                      <td>${Math.round(alloc.subtotal).toLocaleString("es-CL")}</td>
                      <td>${Math.round(alloc.facilitation_fee).toLocaleString("es-CL")}</td>
                      <td><span className={`status-badge status-${alloc.status}`}>{alloc.status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
