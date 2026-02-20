import React, { useEffect, useState } from "react";
import client from "../api/client";
import useGeolocation from "../hooks/useGeolocation";
import PharmacyMap from "../components/PharmacyMap";

const CHAIN_NAMES = {
  cruz_verde: "Cruz Verde",
  salcobrand: "Salcobrand",
  ahumada: "Ahumada",
  dr_simi: "Dr. Simi",
};

export default function PharmacyMapPage() {
  const { location } = useGeolocation();
  const [pharmacies, setPharmacies] = useState([]);

  useEffect(() => {
    if (!location) return;
    client.get(`/pharmacies/nearby?lat=${location.lat}&lng=${location.lng}&radius_km=10`)
      .then(({ data }) => setPharmacies(data))
      .catch(console.error);
  }, [location]);

  if (!location) {
    return (
      <div className="loading-state">
        <div className="spinner"></div>
        <p>Obteniendo ubicación...</p>
      </div>
    );
  }

  return (
    <div className="pharmacy-map-page">
      <div className="container">
        <h2 className="page-title">Farmacias cercanas</h2>

        <div className="map-wrapper">
          <PharmacyMap center={location} pharmacies={pharmacies} />
        </div>

        {pharmacies.length > 0 && (
          <div className="pharmacy-list">
            {pharmacies.map((p) => (
              <div key={p.id} className="pharmacy-item">
                <div className={`chain-logo ${p.chain}`}>
                  {(CHAIN_NAMES[p.chain] || p.chain).slice(0, 2).toUpperCase()}
                </div>
                <div className="pharmacy-item-info">
                  <h3>{p.name}</h3>
                  <p>{p.address}, {p.comuna}</p>
                  {p.distance_km != null && <span className="dist">📍 {p.distance_km.toFixed(1)} km</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
