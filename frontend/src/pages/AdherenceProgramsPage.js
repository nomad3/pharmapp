import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import useAdherence from "../hooks/useAdherence";

export default function AdherenceProgramsPage() {
  const navigate = useNavigate();
  const { programs, loading, enroll } = useAdherence();
  const [enrollMsg, setEnrollMsg] = useState("");

  const handleEnroll = async (programId) => {
    const token = localStorage.getItem("token");
    if (!token) {
      navigate("/login");
      return;
    }
    try {
      await enroll(programId);
      setEnrollMsg("Inscripción exitosa. Ve a tu dashboard para ver tu progreso.");
    } catch (err) {
      setEnrollMsg(err.response?.data?.detail || "Error al inscribirse");
    }
  };

  if (loading) {
    return <div className="loading-state"><div className="spinner"></div><p>Cargando programas...</p></div>;
  }

  return (
    <div className="adherence-programs-page">
      <div className="container">
        <div className="transparency-hero">
          <h1>Programas de Adherencia</h1>
          <p className="transparency-subtitle">
            Recibe descuentos progresivos al mantener tu tratamiento al día. Mientras más constante seas, más ahorras.
          </p>
        </div>

        {enrollMsg && <p className="alert-msg" style={{ textAlign: "center", marginBottom: "1.5rem" }}>{enrollMsg}</p>}

        <div className="programs-grid">
          {programs.map((program) => (
            <div key={program.id} className="program-card">
              <div className="program-card__header">
                <h2>{program.name}</h2>
                <span className={`program-card__type program-type--${program.program_type}`}>
                  {program.program_type === "sponsored" ? "Patrocinado" : "Plataforma"}
                </span>
              </div>
              <div className="program-card__details">
                <div className="program-card__detail">
                  <span className="detail-label">Intervalo de recarga</span>
                  <span className="detail-value">{program.refill_interval_days} días</span>
                </div>
                <div className="program-card__detail">
                  <span className="detail-label">Descuento máximo</span>
                  <span className="detail-value">{Math.round(program.max_discount_pct * 100)}%</span>
                </div>
                <div className="program-card__detail">
                  <span className="detail-label">Período de gracia</span>
                  <span className="detail-value">{program.grace_period_days} días</span>
                </div>
              </div>
              <button className="btn btn--primary" onClick={() => handleEnroll(program.id)}>
                Inscribirme
              </button>
            </div>
          ))}
        </div>

        {programs.length === 0 && (
          <p className="empty-state" style={{ textAlign: "center" }}>No hay programas disponibles aún.</p>
        )}
      </div>
    </div>
  );
}
