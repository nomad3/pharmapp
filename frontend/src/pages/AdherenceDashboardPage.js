import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import useAdherence from "../hooks/useAdherence";
import AdherenceScoreGauge from "../components/AdherenceScoreGauge";

export default function AdherenceDashboardPage() {
  const navigate = useNavigate();
  const { dashboard, loading, loadDashboard, loadEnrollments } = useAdherence();

  useEffect(() => {
    loadDashboard();
    loadEnrollments();
  }, [loadDashboard, loadEnrollments]);

  if (loading) {
    return <div className="loading-state"><div className="spinner"></div><p>Cargando dashboard...</p></div>;
  }

  if (!dashboard) {
    return (
      <div className="container" style={{ textAlign: "center", paddingTop: "3rem" }}>
        <h2>No tienes inscripciones activas</h2>
        <p>Explora los programas disponibles para empezar a ahorrar.</p>
        <button className="btn btn--primary" onClick={() => navigate("/adherence")}>
          Ver programas
        </button>
      </div>
    );
  }

  return (
    <div className="adherence-dashboard-page">
      <div className="container">
        <h1>Mi Adherencia</h1>

        <div className="transparency-stats-grid">
          <div className="summary-card">
            <div className="summary-card__value">{Math.round(dashboard.avg_adherence_score)}</div>
            <div className="summary-card__label">Score promedio</div>
          </div>
          <div className="summary-card">
            <div className="summary-card__value">${Math.round(dashboard.total_savings).toLocaleString("es-CL")}</div>
            <div className="summary-card__label">Ahorro total</div>
          </div>
          <div className="summary-card">
            <div className="summary-card__value">{dashboard.enrollments.length}</div>
            <div className="summary-card__label">Programas activos</div>
          </div>
        </div>

        <div className="enrollment-cards">
          {dashboard.enrollments.map((enrollment) => {
            const daysUntil = enrollment.next_refill_due
              ? Math.ceil((new Date(enrollment.next_refill_due) - new Date()) / (1000 * 60 * 60 * 24))
              : null;

            return (
              <div
                key={enrollment.enrollment_id}
                className="enrollment-card"
                onClick={() => navigate(`/adherence/enrollment/${enrollment.enrollment_id}`)}
              >
                <div className="enrollment-card__left">
                  <AdherenceScoreGauge score={enrollment.adherence_score} size={80} />
                </div>
                <div className="enrollment-card__center">
                  <h3>{enrollment.program_name}</h3>
                  <div className="enrollment-card__stats">
                    <span>Racha: {enrollment.consecutive_on_time} refills</span>
                    <span>Descuento: {Math.round(enrollment.current_discount_pct * 100)}%</span>
                    <span>Ahorrado: ${Math.round(enrollment.total_savings).toLocaleString("es-CL")}</span>
                  </div>
                </div>
                <div className="enrollment-card__right">
                  {daysUntil !== null && (
                    <div className={`refill-countdown ${daysUntil <= 3 ? "refill-countdown--urgent" : ""}`}>
                      <div className="refill-countdown__days">{daysUntil}</div>
                      <div className="refill-countdown__label">días para refill</div>
                    </div>
                  )}
                  <button className="btn btn--primary btn--sm" onClick={(e) => { e.stopPropagation(); navigate(`/medication/${enrollment.medication_id}`); }}>
                    Recargar
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
