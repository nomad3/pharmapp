import React, { useEffect, useState, useCallback } from "react";
import { Helmet } from "react-helmet-async";
import { useSearchParams, Link } from "react-router-dom";
import client from "../api/client";
import SearchFilters from "../components/SearchFilters";

const PAGE_SIZE = 50;

export default function SearchResultsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const q = searchParams.get("q") || "";
  const offset = parseInt(searchParams.get("offset") || "0", 10);

  const [filters, setFilters] = useState({
    form: searchParams.get("form") || "",
    requires_prescription: searchParams.get("requires_prescription") || "",
    chain: searchParams.get("chain") || "",
    price_min: searchParams.get("price_min") || "",
    price_max: searchParams.get("price_max") || "",
  });

  const [results, setResults] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  const fetchResults = useCallback(async (query, currentFilters, currentOffset) => {
    if (!query) return;
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("q", query);
      params.set("limit", String(PAGE_SIZE));
      params.set("offset", String(currentOffset));
      if (currentFilters.form) params.set("form", currentFilters.form);
      if (currentFilters.requires_prescription) params.set("requires_prescription", currentFilters.requires_prescription);
      if (currentFilters.chain) params.set("chain", currentFilters.chain);
      if (currentFilters.price_min) params.set("price_min", currentFilters.price_min);
      if (currentFilters.price_max) params.set("price_max", currentFilters.price_max);

      const { data } = await client.get(`/medications/search?${params.toString()}`);

      if (Array.isArray(data)) {
        setResults(data);
        setTotal(data.length);
      } else {
        setResults(data.items || data.results || []);
        setTotal(data.total ?? (data.items || data.results || []).length);
      }
    } catch (err) {
      console.error(err);
      setResults([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchResults(q, filters, offset);
  }, [q, filters, offset, fetchResults]);

  const updateURL = (newFilters, newOffset) => {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (newFilters.form) params.set("form", newFilters.form);
    if (newFilters.requires_prescription) params.set("requires_prescription", newFilters.requires_prescription);
    if (newFilters.chain) params.set("chain", newFilters.chain);
    if (newFilters.price_min) params.set("price_min", newFilters.price_min);
    if (newFilters.price_max) params.set("price_max", newFilters.price_max);
    if (newOffset > 0) params.set("offset", String(newOffset));
    setSearchParams(params, { replace: true });
  };

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
    updateURL(newFilters, 0);
  };

  const handlePageChange = (newOffset) => {
    updateURL(filters, newOffset);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  if (loading) {
    return (
      <div className="loading-state">
        <div className="spinner"></div>
        <p>Buscando "{q}"...</p>
      </div>
    );
  }

  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
  const hasNext = results.length === PAGE_SIZE;
  const hasPrev = offset > 0;

  return (
    <div className="search-results">
      <Helmet>
        <title>{`"${q}" \u2014 Buscar medicamentos | Remedia`}</title>
        <meta name="description" content={`Resultados para "${q}" en farmacias de Chile.`} />
      </Helmet>
      <div className="container">
        <div className="results-header">
          <h2>Resultados para "{q}"</h2>
          <p className="search-results-count">
            {total > 0
              ? `${total} medicamento${total !== 1 ? "s" : ""} encontrado${total !== 1 ? "s" : ""}`
              : "Sin resultados"}
            {currentPage > 1 && ` \u2014 P\u00e1gina ${currentPage}`}
          </p>
        </div>

        <SearchFilters filters={filters} onFilterChange={handleFilterChange} />

        {results.length === 0 ? (
          <div className="no-results">
            <div className="no-results-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            </div>
            <h3>No encontramos resultados</h3>
            <p>Intenta buscar con otro nombre o principio activo</p>
          </div>
        ) : (
          <>
            <div className="results-grid">
              {results.map((med) => (
                <Link to={`/medicamento/${med.slug || med.id}`} className="med-card" key={med.id}>
                  <div className="med-card-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10.5 1.5H8.25A2.25 2.25 0 0 0 6 3.75v16.5a2.25 2.25 0 0 0 2.25 2.25h7.5A2.25 2.25 0 0 0 18 20.25V3.75a2.25 2.25 0 0 0-2.25-2.25H13.5m-3 0V3h3V1.5m-3 0h3m-6 9h6m-6 4h6"/></svg>
                  </div>
                  <h3>{med.name}</h3>
                  <p className="med-info">{med.active_ingredient}{med.dosage ? ` \u00B7 ${med.dosage}` : ""}</p>
                  <div className="med-details">
                    {med.form && <span className="med-tag">{med.form}</span>}
                    {med.lab && <span className="med-tag">{med.lab}</span>}
                    {med.requires_prescription && <span className="rx-badge">Receta</span>}
                  </div>
                  <div className="view-prices">
                    Comparar precios &rarr;
                  </div>
                </Link>
              ))}
            </div>

            {(hasPrev || hasNext) && (
              <div className="pagination">
                <button disabled={!hasPrev} onClick={() => handlePageChange(offset - PAGE_SIZE)}>
                  &larr; Anterior
                </button>
                <span className="pagination-info">P&aacute;gina {currentPage}</span>
                <button disabled={!hasNext} onClick={() => handlePageChange(offset + PAGE_SIZE)}>
                  Siguiente &rarr;
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
