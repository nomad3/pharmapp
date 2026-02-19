import React from "react";
import SearchBar from "../components/SearchBar";
import useGeolocation from "../hooks/useGeolocation";

export default function HomePage() {
  const { location, error, loading } = useGeolocation();

  return (
    <div className="home-page">
      <h1>PharmApp</h1>
      <p>Encuentra los medicamentos más baratos cerca de ti</p>
      <SearchBar />
      {loading && <p>Obteniendo tu ubicación...</p>}
      {error && <p>No pudimos obtener tu ubicación: {error}</p>}
      {location && <p>Ubicación detectada</p>}
    </div>
  );
}
