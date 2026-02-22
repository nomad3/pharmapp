import React, { useEffect, useState } from "react";
import client from "../api/client";

export default function PharmacyPartnerPage() {
  const [summary, setSummary] = useState([]);
  const [commissions, setCommissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("summary");

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [s, c] = await Promise.all([
        client.get("/commissions/summary"),
        client.get("/commissions/?limit=50"),
      ]);
      setSummary(s.data);
      setCommissions(c.data);
    } catch (e) {
      console.error("Failed to load commissions", e);
    }
    setLoading(false);
  }

  const handleExport = () => {
    window.open("/api/v1/commissions/export", "_blank");
  };

  if (loading) {
    return (
      <div className="loading-state">
        <div className="spinner"></div>
        <p>Cargando comisiones...</p>
      </div>
    );
  }

  const totalCommission = summary.reduce((sum, s) => sum + s.total_commission, 0);
  const totalOrders = summary.reduce((sum, s) => sum + s.total_orders, 0);

  return (
    <div className="partner-page">
      <div className="container">
        <div className="partner-header">
          <h1 className="page-title">Comisiones de Farmacias</h1>
          <button className="btn btn--secondary" onClick={handleExport}>
            Exportar CSV
          </button>
        </div>

        <div className="partner-stats">
          <div className="stat-card">
            <div className="stat-card__value">${Math.round(totalCommission).toLocaleString("es-CL")}</div>
            <div className="stat-card__label">Total comisiones</div>
          </div>
          <div className="stat-card">
            <div className="stat-card__value">{totalOrders}</div>
            <div className="stat-card__label">Total órdenes</div>
          </div>
          <div className="stat-card">
            <div className="stat-card__value">{summary.length}</div>
            <div className="stat-card__label">Farmacias activas</div>
          </div>
        </div>

        <div className="partner-tabs">
          <button className={`tab-btn ${tab === "summary" ? "active" : ""}`} onClick={() => setTab("summary")}>
            Resumen mensual
          </button>
          <button className={`tab-btn ${tab === "detail" ? "active" : ""}`} onClick={() => setTab("detail")}>
            Detalle
          </button>
        </div>

        {tab === "summary" ? (
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Farmacia</th>
                  <th>Mes</th>
                  <th>Órdenes</th>
                  <th>Monto total</th>
                  <th>Comisión</th>
                </tr>
              </thead>
              <tbody>
                {summary.map((s, i) => (
                  <tr key={i}>
                    <td>{s.pharmacy_name || "—"}</td>
                    <td>{s.month}</td>
                    <td>{s.total_orders}</td>
                    <td>${Math.round(s.total_order_amount).toLocaleString("es-CL")}</td>
                    <td>${Math.round(s.total_commission).toLocaleString("es-CL")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Orden total</th>
                  <th>Tasa</th>
                  <th>Comisión</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {commissions.map((c) => (
                  <tr key={c.id}>
                    <td>{c.created_at ? c.created_at.slice(0, 10) : "—"}</td>
                    <td>${Math.round(c.order_total).toLocaleString("es-CL")}</td>
                    <td>{(c.commission_rate * 100).toFixed(1)}%</td>
                    <td>${Math.round(c.commission_amount).toLocaleString("es-CL")}</td>
                    <td><span className={`status-badge status--${c.status}`}>{c.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
