import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client from "../api/client";
import OrderStatusBadge from "../components/OrderStatusBadge";

export default function OrderHistoryPage() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    client.get("/orders/")
      .then(({ data }) => setOrders(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="loading-state">
        <div className="spinner"></div>
        <p>Cargando pedidos...</p>
      </div>
    );
  }

  return (
    <div className="order-history">
      <div className="container">
        <h2 className="page-title">Mis pedidos</h2>

        {orders.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📦</div>
            <h3>No tienes pedidos aún</h3>
            <p>Busca un medicamento y haz tu primera compra por WhatsApp</p>
            <Link to="/">Buscar medicamentos →</Link>
          </div>
        ) : (
          <div className="order-list">
            {orders.map((order) => (
              <Link key={order.id} to={`/orders/${order.id}`} className="order-card" style={{ textDecoration: "none", color: "inherit" }}>
                <div className="order-card-info">
                  <h3>Pedido #{order.id.slice(0, 8)}</h3>
                  <span className="order-date">
                    {new Date(order.created_at).toLocaleDateString("es-CL", { day: "numeric", month: "short", year: "numeric" })}
                  </span>
                </div>
                <div className="order-card-right">
                  <span className="order-total">${order.total.toLocaleString("es-CL")}</span>
                  <OrderStatusBadge status={order.status} />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
