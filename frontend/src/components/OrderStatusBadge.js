import React from "react";

const STATUS_LABELS = {
  pending: "Pendiente",
  payment_sent: "Pago enviado",
  confirmed: "Confirmado",
  delivering: "En camino",
  completed: "Completado",
  cancelled: "Cancelado",
};

export default function OrderStatusBadge({ status }) {
  return <span className={`status-badge status-${status}`}>{STATUS_LABELS[status] || status}</span>;
}
