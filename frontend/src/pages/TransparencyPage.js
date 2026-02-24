import React, { useEffect, useState } from "react";
import { Helmet } from "react-helmet-async";
import { useNavigate } from "react-router-dom";
import client from "../api/client";
import MarkupChart from "../components/charts/MarkupChart";

export default function TransparencyPage() {
  const navigate = useNavigate();
  const [overpriced, setOverpriced] = useState([]);
  const [pharmacyIndex, setPharmacyIndex] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [op, pi, st] = await Promise.all([
          client.get("/transparency/most-overpriced?limit=50"),
          client.get("/transparency/pharmacy-index"),
          client.get("/transparency/stats"),
        ]);
        setOverpriced(op.data);
        setPharmacyIndex(pi.data);
        setStats(st.data);
      } catch (err) {
        console.error("Error loading transparency data:", err);
      }
      setLoading(false);
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="loading-state">
        <div className="spinner"></div>
        <p>Cargando datos de transparencia...</p>
      </div>
    );
  }

  return (
    <div className="transparency-page">
      <Helmet>
        <title>Transparencia de precios | Remedia</title>
        <meta name="description" content="Compara precios de Cenabast vs farmacias. Descubre cuánto margen cobran las cadenas sobre el costo del Estado." />
      </Helmet>
      <div className="container">
        <div className="transparency-hero">
          <h1>Transparencia de Precios</h1>
          <p className="transparency-subtitle">
            Compara lo que pagas en farmacia vs. lo que cuesta al Estado comprar el mismo medicamento a travs de Cenabast.
          </p>
        </div>

        {stats && (
          <div className="transparency-stats-grid">
            <div className="summary-card">
              <div className="summary-card__value">{stats.avg_markup_pct}%</div>
              <div className="summary-card__label">Markup promedio</div>
            </div>
            <div className="summary-card">
              <div className="summary-card__value">${stats.avg_cenabast_cost?.toLocaleString("es-CL")}</div>
              <div className="summary-card__label">Costo promedio Cenabast</div>
            </div>
            <div className="summary-card">
              <div className="summary-card__value">${stats.avg_retail_price?.toLocaleString("es-CL")}</div>
              <div className="summary-card__label">Precio promedio retail</div>
            </div>
            <div className="summary-card">
              <div className="summary-card__value">{stats.medications_with_transparency}</div>
              <div className="summary-card__label">Medicamentos con datos</div>
            </div>
          </div>
        )}

        {pharmacyIndex.length > 0 && (
          <section className="transparency-section">
            <h2>Indice de Transparencia por Cadena</h2>
            <MarkupChart data={pharmacyIndex} />
          </section>
        )}

        <section className="transparency-section">
          <h2>Medicamentos con Mayor Sobreprecio</h2>
          <div className="data-table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Medicamento</th>
                  <th>Principio Activo</th>
                  <th>Costo Cenabast</th>
                  <th>Precio Retail</th>
                  <th>Sobreprecio</th>
                </tr>
              </thead>
              <tbody>
                {overpriced.map((med) => (
                  <tr
                    key={med.medication_id}
                    className="clickable-row"
                    onClick={() => navigate(`/medication/${med.medication_id}`)}
                  >
                    <td className="med-name-cell">{med.medication_name}</td>
                    <td>{med.active_ingredient}</td>
                    <td>${Math.round(med.cenabast_cost).toLocaleString("es-CL")}</td>
                    <td>${Math.round(med.avg_retail).toLocaleString("es-CL")}</td>
                    <td>
                      <span className={`markup-badge ${med.markup_pct > 500 ? "markup-extreme" : med.markup_pct > 200 ? "markup-high" : "markup-moderate"}`}>
                        +{Math.round(med.markup_pct).toLocaleString("es-CL")}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
}
