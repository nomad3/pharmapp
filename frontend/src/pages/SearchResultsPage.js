import React, { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import client from "../api/client";

export default function SearchResultsPage() {
  const [searchParams] = useSearchParams();
  const q = searchParams.get("q") || "";
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!q) return;
    client.get(`/medications/search?q=${encodeURIComponent(q)}`)
      .then(({ data }) => setResults(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [q]);

  if (loading) return <p>Buscando "{q}"...</p>;

  return (
    <div className="search-results">
      <h2>Resultados para "{q}"</h2>
      {results.length === 0 && <p>No se encontraron medicamentos</p>}
      <ul>
        {results.map((med) => (
          <li key={med.id}>
            <Link to={`/medication/${med.id}`}>
              <strong>{med.name}</strong> — {med.active_ingredient} {med.dosage}
              {med.requires_prescription && <span className="rx-badge">Receta</span>}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
