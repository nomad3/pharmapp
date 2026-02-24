import React, { useEffect, useState, useCallback } from "react";
import { Helmet } from "react-helmet-async";
import client from "../../api/client";
import { AdminNav } from "./AdminDashboardPage";

const formatCLP = (n) => `$${Number(n).toLocaleString("es-CL")} CLP`;

const STATUS_LABELS = {
  pending: "Pendiente",
  payment_sent: "Pago Enviado",
  confirmed: "Confirmado",
  delivering: "En Camino",
  completed: "Entregado",
  cancelled: "Cancelado",
};

export default function AdminOrdersPage() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");
  const [expanded, setExpanded] = useState(null);
  const [updating, setUpdating] = useState(null);

  const fetchOrders = useCallback(() => {
    setLoading(true);
    const params = filter ? `?status=${filter}&limit=50` : "?limit=50";
    client
      .get(`/orders/admin/all${params}`)
      .then(({ data }) => setOrders(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [filter]);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

  const updateStatus = (orderId, newStatus) => {
    setUpdating(orderId);
    client
      .patch(`/orders/${orderId}/status`, { status: newStatus })
      .then(() => fetchOrders())
      .catch(console.error)
      .finally(() => setUpdating(null));
  };

  return (
    <div className="admin-page">
      <Helmet>
        <title>Pedidos Admin | Remedia</title>
        <meta name="robots" content="noindex" />
      </Helmet>
      <div className="container">
        <h1 className="page-title">Gestionar Pedidos</h1>
        <AdminNav />

        <div style={{ marginBottom: 20 }}>
          <select
            className="input"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            style={{ minWidth: 200 }}
          >
            <option value="">Todos los estados</option>
            <option value="pending">Pendiente</option>
            <option value="payment_sent">Pago Enviado</option>
            <option value="confirmed">Confirmado</option>
            <option value="delivering">En Camino</option>
            <option value="completed">Entregado</option>
            <option value="cancelled">Cancelado</option>
          </select>
        </div>

        {loading ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Cargando pedidos...</p>
          </div>
        ) : (
          <div className="data-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Estado</th>
                  <th>Total</th>
                  <th>Proveedor</th>
                  <th>Fecha</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((o) => (
                  <React.Fragment key={o.id}>
                    <tr
                      className="clickable-row"
                      onClick={() =>
                        setExpanded(expanded === o.id ? null : o.id)
                      }
                    >
                      <td>
                        <code>{o.id.slice(0, 8)}</code>
                      </td>
                      <td>
                        <span className={`status-badge status-${o.status}`}>
                          {STATUS_LABELS[o.status] || o.status}
                        </span>
                      </td>
                      <td>{formatCLP(o.total)}</td>
                      <td>{o.payment_provider || "-"}</td>
                      <td>
                        {new Date(o.created_at).toLocaleDateString("es-CL", {
                          day: "numeric",
                          month: "short",
                          year: "numeric",
                        })}
                      </td>
                      <td>
                        <div
                          className="admin-actions"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {o.status === "confirmed" && (
                            <button
                              className="btn btn--primary btn--sm"
                              disabled={updating === o.id}
                              onClick={() => updateStatus(o.id, "delivering")}
                            >
                              Confirmar Envio
                            </button>
                          )}
                          {o.status === "delivering" && (
                            <button
                              className="btn btn--primary btn--sm"
                              disabled={updating === o.id}
                              onClick={() => updateStatus(o.id, "completed")}
                            >
                              Marcar Entregado
                            </button>
                          )}
                          {o.status !== "completed" &&
                            o.status !== "cancelled" && (
                              <button
                                className="btn btn--danger btn--sm"
                                disabled={updating === o.id}
                                onClick={() => updateStatus(o.id, "cancelled")}
                              >
                                Cancelar
                              </button>
                            )}
                        </div>
                      </td>
                    </tr>
                    {expanded === o.id && (
                      <tr>
                        <td colSpan={6} style={{ background: "var(--bg)" }}>
                          <div style={{ padding: "12px 8px" }}>
                            <strong>Items del pedido:</strong>
                            {o.items && o.items.length > 0 ? (
                              <ul style={{ marginTop: 8 }}>
                                {o.items.map((item, idx) => (
                                  <li
                                    key={idx}
                                    style={{
                                      padding: "4px 0",
                                      fontSize: 14,
                                    }}
                                  >
                                    {item.medication_name || item.name || `Item ${idx + 1}`}
                                    {" "}x{item.quantity} &mdash;{" "}
                                    {formatCLP(item.unit_price || item.price)}
                                  </li>
                                ))}
                              </ul>
                            ) : (
                              <p style={{ color: "var(--text-secondary)", marginTop: 8, fontSize: 14 }}>
                                Sin detalle de items disponible
                              </p>
                            )}
                            {o.user_phone && (
                              <p style={{ marginTop: 8, fontSize: 13, color: "var(--text-secondary)" }}>
                                Tel: {o.user_phone}
                              </p>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
                {orders.length === 0 && (
                  <tr>
                    <td
                      colSpan={6}
                      style={{ textAlign: "center", padding: 24 }}
                    >
                      No se encontraron pedidos
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
