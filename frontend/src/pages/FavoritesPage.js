import React, { useEffect, useState } from "react";
import client from "../api/client";

export default function FavoritesPage() {
  const [favorites, setFavorites] = useState([]);

  useEffect(() => {
    client.get("/favorites").then(({ data }) => setFavorites(data)).catch(console.error);
  }, []);

  const removeFavorite = async (id) => {
    await client.delete(`/favorites/${id}`);
    setFavorites(favorites.filter((f) => f.id !== id));
  };

  return (
    <div className="favorites-page">
      <h2>Mis favoritos</h2>
      {favorites.map((fav) => (
        <div key={fav.id}>
          <span>{fav.medication_id}</span>
          <button onClick={() => removeFavorite(fav.id)}>Eliminar</button>
        </div>
      ))}
    </div>
  );
}
