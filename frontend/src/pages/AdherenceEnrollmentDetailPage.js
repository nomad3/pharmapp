import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import client from "../api/client";
import AdherenceScoreGauge from "../components/AdherenceScoreGauge";
import DiscountTierProgress from "../components/DiscountTierProgress";
import RefillTimeline from "../components/RefillTimeline";

export default function AdherenceEnrollmentDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [enrollment, setEnrollment] = useState(null);
  const [refills, setRefills] = useState([]);
  const [programTiers, setProgramTiers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [enrollRes, refillsRes] = await Promise.all([
          client.get("/adherence/enrollments"),
          client.get(`/adherence/enrollment/${id}/refills`),
        ]);
        const found = enrollRes.data.find((e) => e.id === id);
        setEnrollment(found);
        setRefills(refillsRes.data);

        if (found) {
          try {
            const { data } = await client.get(`/adherence/programs/${found.program_id}`);
            setProgramTiers(data.tiers || []);
          } catch (e) { /* no tiers */ }
        }
      } catch (err) {
        console.error("Error loading enrollment:", err);
      }
      setLoading(false);
    };
    fetchData();
  }, [id]);

  if (loading) {
    return <div className="loading-state"><div className="spinner"></div></div>;
  }

  if (!enrollment) {
    return <div className="container"><p>Inscripción no encontrada.</p></div>;
  }

  const totalSavings = refills.reduce((acc, r) => acc + (r.discount_amount || 0), 0);

  return (
    <div className="adherence-detail-page">
      <div className="container">
        <button className="btn btn--secondary btn--sm" onClick={() => navigate("/adherence/dashboard")} style={{ marginBottom: "1rem" }}>
          Volver al dashboard
        </button>

        <div className="adherence-detail__header">
          <AdherenceScoreGauge score={enrollment.adherence_score} size={160} />
          <div className="adherence-detail__info">
            <h1>Programa de Adherencia</h1>
            <div className="adherence-detail__stats">
              <div className="stat-item">
                <span className="stat-item__value">{enrollment.consecutive_on_time}</span>
                <span className="stat-item__label">Racha actual</span>
              </div>
              <div className="stat-item">
                <span className="stat-item__value">{Math.round(enrollment.current_discount_pct * 100)}%</span>
                <span className="stat-item__label">Descuento actual</span>
              </div>
              <div className="stat-item">
                <span className="stat-item__value">${Math.round(totalSavings).toLocaleString("es-CL")}</span>
                <span className="stat-item__label">Ahorro total</span>
              </div>
              <div className="stat-item">
                <span className="stat-item__value">{enrollment.total_refills || 0}</span>
                <span className="stat-item__label">Total refills</span>
              </div>
            </div>
          </div>
        </div>

        <section className="adherence-section">
          <h2>Progreso de Descuento</h2>
          <DiscountTierProgress
            currentRefills={enrollment.consecutive_on_time}
            tiers={programTiers}
            currentDiscount={enrollment.current_discount_pct}
          />
        </section>

        <section className="adherence-section">
          <h2>Historial de Refills</h2>
          <RefillTimeline refills={refills} />
        </section>
      </div>
    </div>
  );
}
