import React, { useEffect, useState } from "react";
import { Helmet } from "react-helmet-async";
import { Link, useLocation } from "react-router-dom";
import client from "../../api/client";

const formatCLP = (n) => `$${Number(n).toLocaleString("es-CL")} CLP`;

function AdminNav() {
  const location = useLocation();
  const links = [
    { to: "/admin", label: "Dashboard" },
    { to: "/admin/orders", label: "Pedidos" },
    { to: "/admin/users", label: "Usuarios" },
    { to: "/admin/scraping", label: "Scraping" },
    { to: "/admin/settings", label: "Configuracion" },
  ];
  return (
    <nav className="admin-nav">
      {links.map((l) => (
        <Link
          key={l.to}
          to={l.to}
          className={location.pathname === l.to ? "active" : ""}
        >
          {l.label}
        </Link>
      ))}
    </nav>
  );
}

export { AdminNav };

export default function AdminDashboardPage() {
  const [stats, setStats] = useState(null);
  const [orders, setOrders] = useState([]);
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      client.get("/admin/stats").then(({ data }) => setStats(data)),
      client.get("/orders/admin/all?limit=10").then(({ data }) => setOrders(data)),
      client.get("/scraping/runs?limit=5").then(({ data }) => setRuns(data)),
    ])
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="loading-state">
        <div className="spinner"></div>
        <p>Cargando panel...</p>
      </div>
    );
  }

  return (
    <div className="admin-page">
      <Helmet>
        <title>Panel de Administracion | Remedia</title>
        <meta name="robots" content="noindex" />
      </Helmet>
      <div className="container">
        <h1 className="page-title">Panel de Administracion</h1>
        <AdminNav />

        {stats && (
          <>
            <div className="admin-grid">
              <div className="stat-card">
                <span className="stat-value">{stats.total_users}</span>
                <span className="stat-label">Usuarios</span>
              </div>
              <div className="stat-card">
                <span className="stat-value">{stats.orders_today}</span>
                <span className="stat-label">Pedidos Hoy</span>
              </div>
              <div className="stat-card">
                <span className="stat-value">{formatCLP(stats.total_revenue)}</span>
                <span className="stat-label">Ingresos Totales</span>
              </div>
              <div className="stat-card">
                <span className="stat-value">{stats.total_medications}</span>
                <span className="stat-label">Medicamentos</span>
              </div>
            </div>
            <div className="admin-grid" style={{ marginTop: 16 }}>
              <div className="stat-card">
                <span className="stat-value">{stats.total_pharmacies}</span>
                <span className="stat-label">Farmacias</span>
              </div>
              <div className="stat-card">
                <span className="stat-value">{stats.total_prices}</span>
                <span className="stat-label">Precios</span>
              </div>
              <div className="stat-card">
                <span className="stat-value">
                  {stats.payment_success_rate != null
                    ? `${(stats.payment_success_rate * 100).toFixed(1)}%`
                    : "N/A"}
                </span>
                <span className="stat-label">Tasa de Pago</span>
              </div>
              <div className="stat-card">
                <span className="stat-value">{stats.total_orders}</span>
                <span className="stat-label">Pedidos Totales</span>
              </div>
            </div>
          </>
        )}

        <h2 style={{ fontSize: 18, fontWeight: 600, margin: "32px 0 12px" }}>
          Pedidos Recientes
        </h2>
        <div className="data-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Estado</th>
                <th>Total</th>
                <th>Proveedor</th>
                <th>Fecha</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id}>
                  <td>
                    <code>{o.id.slice(0, 8)}</code>
                  </td>
                  <td>
                    <span className={`status-badge status-${o.status}`}>
                      {o.status}
                    </span>
                  </td>
                  <td>{formatCLP(o.total)}</td>
                  <td>{o.payment_provider || "-"}</td>
                  <td>
                    {new Date(o.created_at).toLocaleDateString("es-CL", {
                      day: "numeric",
                      month: "short",
                    })}
                  </td>
                </tr>
              ))}
              {orders.length === 0 && (
                <tr>
                  <td colSpan={5} style={{ textAlign: "center", padding: 24 }}>
                    Sin pedidos
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <h2 style={{ fontSize: 18, fontWeight: 600, margin: "32px 0 12px" }}>
          Scraping Reciente
        </h2>
        <div className="data-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Cadena</th>
                <th>Estado</th>
                <th>Productos</th>
                <th>Errores</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r, i) => (
                <tr key={i}>
                  <td>{r.chain}</td>
                  <td>
                    <span
                      className={`status-badge ${
                        r.status === "completed"
                          ? "status-completed"
                          : r.status === "running"
                          ? "status-delivering"
                          : "status-cancelled"
                      }`}
                    >
                      {r.status}
                    </span>
                  </td>
                  <td>{r.products_found ?? "-"}</td>
                  <td>{r.errors ?? 0}</td>
                </tr>
              ))}
              {runs.length === 0 && (
                <tr>
                  <td colSpan={4} style={{ textAlign: "center", padding: 24 }}>
                    Sin ejecuciones
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
