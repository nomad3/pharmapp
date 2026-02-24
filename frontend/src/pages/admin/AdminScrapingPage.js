import React, { useEffect, useState, useCallback } from "react";
import { Helmet } from "react-helmet-async";
import client from "../../api/client";
import { AdminNav } from "./AdminDashboardPage";

const CHAINS = ["cruz_verde", "salcobrand", "ahumada", "dr_simi"];

const CHAIN_LABELS = {
  cruz_verde: "Cruz Verde",
  salcobrand: "Salcobrand",
  ahumada: "Ahumada",
  dr_simi: "Dr. Simi",
};

export default function AdminScrapingPage() {
  const [runs, setRuns] = useState([]);
  const [schedule, setSchedule] = useState(null);
  const [loading, setLoading] = useState(true);
  const [triggeringAll, setTriggeringAll] = useState(false);
  const [triggeringChain, setTriggeringChain] = useState(null);

  const fetchData = useCallback(() => {
    setLoading(true);
    Promise.all([
      client.get("/scraping/runs?limit=20").then(({ data }) => setRuns(data)),
      client
        .get("/scraping/schedule")
        .then(({ data }) => setSchedule(data))
        .catch(() => setSchedule(null)),
    ])
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const triggerScrape = (chain) => {
    if (chain) {
      setTriggeringChain(chain);
      client
        .post(`/scraping/catalog?chains=${chain}`)
        .then(() => {
          setTimeout(fetchData, 2000);
        })
        .catch(console.error)
        .finally(() => setTriggeringChain(null));
    } else {
      setTriggeringAll(true);
      client
        .post("/scraping/catalog")
        .then(() => {
          setTimeout(fetchData, 2000);
        })
        .catch(console.error)
        .finally(() => setTriggeringAll(false));
    }
  };

  const getLastRun = (chain) => {
    return runs.find((r) => r.chain === chain) || null;
  };

  const formatDuration = (seconds) => {
    if (!seconds) return "-";
    if (seconds < 60) return `${seconds}s`;
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}m ${s}s`;
  };

  if (loading) {
    return (
      <div className="loading-state">
        <div className="spinner"></div>
        <p>Cargando datos de scraping...</p>
      </div>
    );
  }

  return (
    <div className="admin-page">
      <Helmet>
        <title>Scraping Admin | Remedia</title>
        <meta name="robots" content="noindex" />
      </Helmet>
      <div className="container">
        <h1 className="page-title">Scraping de Precios</h1>
        <AdminNav />

        {schedule && (
          <div className="chain-card" style={{ marginBottom: 24 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>
              Programacion
            </h3>
            <p style={{ fontSize: 14, color: "var(--text-secondary)" }}>
              {schedule.next_run
                ? `Proxima ejecucion: ${new Date(schedule.next_run).toLocaleString("es-CL")}`
                : "Sin programacion activa"}
            </p>
            {schedule.last_run && (
              <p style={{ fontSize: 14, color: "var(--text-secondary)", marginTop: 4 }}>
                Ultima ejecucion:{" "}
                {new Date(schedule.last_run).toLocaleString("es-CL")}
                {schedule.last_status && ` (${schedule.last_status})`}
              </p>
            )}
          </div>
        )}

        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: 20,
          }}
        >
          <h2 style={{ fontSize: 18, fontWeight: 600 }}>Cadenas</h2>
          <button
            className="btn btn--primary"
            disabled={triggeringAll}
            onClick={() => triggerScrape(null)}
          >
            {triggeringAll ? "Ejecutando..." : "Ejecutar Todas"}
          </button>
        </div>

        <div className="admin-grid">
          {CHAINS.map((chain) => {
            const last = getLastRun(chain);
            return (
              <div className="chain-card" key={chain}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    marginBottom: 12,
                  }}
                >
                  <h3 style={{ fontSize: 15, fontWeight: 600 }}>
                    {CHAIN_LABELS[chain]}
                  </h3>
                  {last && (
                    <span
                      className={`status-badge ${
                        last.status === "completed"
                          ? "status-completed"
                          : last.status === "running"
                          ? "status-delivering"
                          : "status-cancelled"
                      }`}
                    >
                      {last.status}
                    </span>
                  )}
                </div>
                {last ? (
                  <div style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 12 }}>
                    <p>Productos: {last.products_found ?? "-"}</p>
                    <p>Errores: {last.errors ?? 0}</p>
                    <p>
                      Fecha:{" "}
                      {new Date(last.started_at || last.created_at).toLocaleString("es-CL")}
                    </p>
                  </div>
                ) : (
                  <p style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 12 }}>
                    Sin ejecuciones previas
                  </p>
                )}
                <button
                  className="run-now-btn"
                  disabled={triggeringChain === chain}
                  onClick={() => triggerScrape(chain)}
                >
                  {triggeringChain === chain ? "Ejecutando..." : "Ejecutar Ahora"}
                </button>
              </div>
            );
          })}
        </div>

        <h2 style={{ fontSize: 18, fontWeight: 600, margin: "32px 0 12px" }}>
          Historial de Ejecuciones
        </h2>
        <div className="data-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Cadena</th>
                <th>Estado</th>
                <th>Productos</th>
                <th>Precios</th>
                <th>Errores</th>
                <th>Inicio</th>
                <th>Duracion</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r, i) => (
                <tr key={i}>
                  <td>{CHAIN_LABELS[r.chain] || r.chain}</td>
                  <td>
                    <span
                      className={`status-badge ${
                        r.status === "completed"
                          ? "status-completed"
                          : r.status === "running"
                          ? "status-delivering"
                          : "status-cancelled"
                      }`}
                    >
                      {r.status}
                    </span>
                  </td>
                  <td>{r.products_found ?? "-"}</td>
                  <td>{r.prices_upserted ?? "-"}</td>
                  <td>{r.errors ?? 0}</td>
                  <td>
                    {r.started_at || r.created_at
                      ? new Date(
                          r.started_at || r.created_at
                        ).toLocaleString("es-CL")
                      : "-"}
                  </td>
                  <td>{formatDuration(r.duration_seconds)}</td>
                </tr>
              ))}
              {runs.length === 0 && (
                <tr>
                  <td colSpan={7} style={{ textAlign: "center", padding: 24 }}>
                    Sin ejecuciones
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
