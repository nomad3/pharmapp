import React, { useEffect, useState } from "react";
import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import client from "../api/client";

export default function FavoritesPage() {
  const [favorites, setFavorites] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isPremium, setIsPremium] = useState(false);
  const [tab, setTab] = useState("favorites");

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      client.get("/premium/status")
        .then(({ data }) => setIsPremium(data.tier === "premium"))
        .catch(() => {});
    }

    client.get("/favorites")
      .then(({ data }) => setFavorites(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (isPremium && tab === "alerts") {
      client.get("/premium/alerts")
        .then(({ data }) => setAlerts(data))
        .catch(console.error);
    }
  }, [isPremium, tab]);

  const removeFavorite = async (id) => {
    await client.delete(`/favorites/${id}`);
    setFavorites(favorites.filter((f) => f.id !== id));
  };

  const deactivateAlert = async (id) => {
    await client.delete(`/premium/alerts/${id}`);
    setAlerts(alerts.map((a) => a.id === id ? { ...a, is_active: false } : a));
  };

  if (loading) {
    return (
      <div className="loading-state">
        <div className="spinner"></div>
        <p>Cargando favoritos...</p>
      </div>
    );
  }

  return (
    <div className="favorites-page">
      <Helmet>
        <title>Mis favoritos | PharmApp</title>
        <meta name="robots" content="noindex" />
      </Helmet>
      <div className="container">
        <h2 className="page-title">Mis favoritos</h2>

        {isPremium && (
          <div className="fav-tabs">
            <button className={`tab-btn ${tab === "favorites" ? "active" : ""}`} onClick={() => setTab("favorites")}>
              Favoritos
            </button>
            <button className={`tab-btn ${tab === "alerts" ? "active" : ""}`} onClick={() => setTab("alerts")}>
              Alertas de precio
            </button>
          </div>
        )}

        {tab === "favorites" ? (
          favorites.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">❤️</div>
              <h3>No tienes favoritos</h3>
              <p>Guarda tus medicamentos frecuentes para acceder rápido a sus precios</p>
              <Link to="/">Buscar medicamentos →</Link>
            </div>
          ) : (
            <div className="favorites-list">
              {favorites.map((fav) => (
                <div key={fav.id} className="fav-card">
                  <div className="fav-card-icon">💊</div>
                  <div className="fav-card-info">
                    <h3>{fav.medication_name || "Medicamento"}</h3>
                    <p>Guardado como favorito</p>
                  </div>
                  <button onClick={() => removeFavorite(fav.id)} className="fav-remove">
                    Eliminar
                  </button>
                </div>
              ))}
            </div>
          )
        ) : (
          <div className="alerts-list">
            {alerts.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">🔔</div>
                <h3>No tienes alertas</h3>
                <p>Crea alertas desde la página de un medicamento para recibir notificaciones de precios</p>
              </div>
            ) : (
              <div className="data-table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Medicamento</th>
                      <th>Precio objetivo</th>
                      <th>Estado</th>
                      <th>Última notificación</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {alerts.map((a) => (
                      <tr key={a.id}>
                        <td>{a.medication_name || "—"}</td>
                        <td>${Math.round(a.target_price).toLocaleString("es-CL")}</td>
                        <td>
                          <span className={`status-badge status--${a.is_active ? "active" : "inactive"}`}>
                            {a.is_active ? "Activa" : "Inactiva"}
                          </span>
                        </td>
                        <td>{a.last_notified_at ? a.last_notified_at.slice(0, 10) : "Nunca"}</td>
                        <td>
                          {a.is_active && (
                            <button className="btn btn--sm btn--danger" onClick={() => deactivateAlert(a.id)}>
                              Desactivar
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
