import React, { useEffect, useState } from "react";
import client from "../api/client";
import useGeolocation from "../hooks/useGeolocation";
import PharmacyMap from "../components/PharmacyMap";

export default function PharmacyMapPage() {
  const { location } = useGeolocation();
  const [pharmacies, setPharmacies] = useState([]);

  useEffect(() => {
    if (!location) return;
    client.get(`/pharmacies/nearby?lat=${location.lat}&lng=${location.lng}&radius_km=5`)
      .then(({ data }) => setPharmacies(data))
      .catch(console.error);
  }, [location]);

  if (!location) return <p>Obteniendo ubicación...</p>;

  return (
    <div className="pharmacy-map-page">
      <h2>Farmacias cercanas</h2>
      <PharmacyMap center={location} pharmacies={pharmacies} />
    </div>
  );
}
