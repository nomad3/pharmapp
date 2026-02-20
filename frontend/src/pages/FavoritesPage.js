import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client from "../api/client";

export default function FavoritesPage() {
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    client.get("/favorites")
      .then(({ data }) => setFavorites(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const removeFavorite = async (id) => {
    await client.delete(`/favorites/${id}`);
    setFavorites(favorites.filter((f) => f.id !== id));
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
      <div className="container">
        <h2 className="page-title">Mis favoritos</h2>

        {favorites.length === 0 ? (
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
        )}
      </div>
    </div>
  );
}
