import React, { useEffect, useState } from "react";
import { Helmet } from "react-helmet-async";
import { useSearchParams, Link } from "react-router-dom";
import client from "../api/client";

export default function SearchResultsPage() {
  const [searchParams] = useSearchParams();
  const q = searchParams.get("q") || "";
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!q) return;
    setLoading(true);
    client.get(`/medications/search?q=${encodeURIComponent(q)}`)
      .then(({ data }) => setResults(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [q]);

  if (loading) {
    return (
      <div className="loading-state">
        <div className="spinner"></div>
        <p>Buscando "{q}"...</p>
      </div>
    );
  }

  return (
    <div className="search-results">
      <Helmet>
        <title>{`"${q}" — Buscar medicamentos | PharmApp`}</title>
        <meta name="description" content={`${results.length} resultados para "${q}" en farmacias de Chile.`} />
      </Helmet>
      <div className="container">
        <div className="results-header">
          <h2>Resultados para "{q}"</h2>
          <p className="results-count">{results.length} medicamento{results.length !== 1 ? "s" : ""} encontrado{results.length !== 1 ? "s" : ""}</p>
        </div>

        {results.length === 0 ? (
          <div className="no-results">
            <div className="no-results-icon">🔍</div>
            <h3>No encontramos resultados</h3>
            <p>Intenta buscar con otro nombre o principio activo</p>
          </div>
        ) : (
          <div className="results-grid">
            {results.map((med) => (
              <Link to={`/medicamento/${med.slug || med.id}`} className="med-card" key={med.id}>
                <div className="med-card-icon">💊</div>
                <h3>{med.name}</h3>
                <p className="med-info">{med.active_ingredient}{med.dosage ? ` · ${med.dosage}` : ""}</p>
                <div className="med-details">
                  {med.form && <span className="med-tag">{med.form}</span>}
                  {med.lab && <span className="med-tag">{med.lab}</span>}
                  {med.requires_prescription && <span className="rx-badge">Receta</span>}
                </div>
                <div className="view-prices">
                  Comparar precios →
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
