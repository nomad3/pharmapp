import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import useGpo from "../hooks/useGpo";
import GpoSidebar from "../components/GpoSidebar";
import DemandAggregationCard from "../components/DemandAggregationCard";

export default function GpoDashboardPage() {
  const { slug } = useParams();
  const { group, members, demand, orders, savings, loading, loadMembers, loadDemand, loadOrders, loadSavings } = useGpo(slug);
  const [currentMonth] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
  });

  useEffect(() => {
    loadMembers();
    loadDemand(currentMonth);
    loadOrders();
    loadSavings();
  }, [loadMembers, loadDemand, loadOrders, loadSavings, currentMonth]);

  if (loading) {
    return (
      <div className="loading-state">
        <div className="spinner"></div>
        <p>Cargando grupo de compra...</p>
      </div>
    );
  }

  if (!group) {
    return <div className="container"><p>Grupo no encontrado.</p></div>;
  }

  const totalSavings = savings.reduce((acc, s) => acc + s.total_savings, 0);

  return (
    <div className="org-layout container">
      <GpoSidebar slug={slug} />
      <div className="org-main">
        <h1>{group.name}</h1>
        <p className="subtitle">Grupo de Compra Colectiva</p>

        <div className="transparency-stats-grid">
          <div className="summary-card">
            <div className="summary-card__value">{members.length}</div>
            <div className="summary-card__label">Miembros</div>
          </div>
          <div className="summary-card">
            <div className="summary-card__value">{orders.length}</div>
            <div className="summary-card__label">Órdenes activas</div>
          </div>
          <div className="summary-card">
            <div className="summary-card__value">${Math.round(totalSavings).toLocaleString("es-CL")}</div>
            <div className="summary-card__label">Ahorro total</div>
          </div>
          <div className="summary-card">
            <div className="summary-card__value">{group.facilitation_fee_rate * 100}%</div>
            <div className="summary-card__label">Fee facilitación</div>
          </div>
        </div>

        <section className="gpo-section">
          <div className="section-header">
            <h2>Demanda Agregada — {currentMonth}</h2>
            <Link to={`/gpo/${slug}/intents`} className="btn btn--primary btn--sm">
              Agregar intención
            </Link>
          </div>
          {demand.length === 0 ? (
            <p className="empty-state">No hay intenciones de compra para este mes.</p>
          ) : (
            <div className="demand-grid">
              {demand.map((item, i) => (
                <DemandAggregationCard key={i} item={item} />
              ))}
            </div>
          )}
        </section>

        <section className="gpo-section">
          <h2>Órdenes Recientes</h2>
          {orders.length === 0 ? (
            <p className="empty-state">No hay órdenes grupales aún.</p>
          ) : (
            <div className="data-table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Producto</th>
                    <th>Mes</th>
                    <th>Cantidad</th>
                    <th>Miembros</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.slice(0, 10).map((order) => (
                    <tr key={order.id} className="clickable-row" onClick={() => window.location.href = `/gpo/${slug}/orders/${order.id}`}>
                      <td>{order.product_name}</td>
                      <td>{order.target_month}</td>
                      <td>{order.total_quantity?.toLocaleString("es-CL")}</td>
                      <td>{order.member_count}</td>
                      <td><span className={`status-badge status-${order.status}`}>{order.status}</span></td>
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
