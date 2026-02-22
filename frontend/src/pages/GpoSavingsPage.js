import React, { useEffect } from "react";
import { useParams } from "react-router-dom";
import useGpo from "../hooks/useGpo";
import GpoSidebar from "../components/GpoSidebar";

export default function GpoSavingsPage() {
  const { slug } = useParams();
  const { group, savings, loading, loadSavings } = useGpo(slug);

  useEffect(() => {
    loadSavings();
  }, [loadSavings]);

  if (loading) {
    return <div className="loading-state"><div className="spinner"></div></div>;
  }

  const totalSavings = savings.reduce((acc, s) => acc + s.total_savings, 0);
  const totalOrders = savings.reduce((acc, s) => acc + s.order_count, 0);

  return (
    <div className="org-layout container">
      <GpoSidebar slug={slug} />
      <div className="org-main">
        <h1>Ahorros del Grupo</h1>

        <div className="transparency-stats-grid">
          <div className="summary-card">
            <div className="summary-card__value">${Math.round(totalSavings).toLocaleString("es-CL")}</div>
            <div className="summary-card__label">Ahorro total</div>
          </div>
          <div className="summary-card">
            <div className="summary-card__value">{totalOrders}</div>
            <div className="summary-card__label">Órdenes completadas</div>
          </div>
          <div className="summary-card">
            <div className="summary-card__value">{savings.length}</div>
            <div className="summary-card__label">Miembros con ahorros</div>
          </div>
        </div>

        <section className="gpo-section">
          <h2>Ahorro por Miembro</h2>
          {savings.length === 0 ? (
            <p className="empty-state">No hay datos de ahorro aún. Completa órdenes grupales para ver los ahorros.</p>
          ) : (
            <div className="data-table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Institución</th>
                    <th>Órdenes</th>
                    <th>Ahorro Total</th>
                  </tr>
                </thead>
                <tbody>
                  {savings.map((s) => (
                    <tr key={s.member_id}>
                      <td>{s.institution_name || s.member_id.slice(0, 8)}</td>
                      <td>{s.order_count}</td>
                      <td className="savings-amount">${Math.round(s.total_savings).toLocaleString("es-CL")}</td>
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
