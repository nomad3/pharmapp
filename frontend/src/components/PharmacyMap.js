import React from "react";
import { GoogleMap, Marker, useJsApiLoader } from "@react-google-maps/api";

const containerStyle = { width: "100%", height: "400px" };

export default function PharmacyMap({ center, pharmacies }) {
  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: process.env.REACT_APP_GOOGLE_MAPS_API_KEY || "",
  });

  if (!isLoaded) return <p>Cargando mapa...</p>;

  return (
    <GoogleMap mapContainerStyle={containerStyle} center={center} zoom={14}>
      {pharmacies.map((p) => (
        <Marker
          key={p.id}
          position={{ lat: p.lat, lng: p.lng }}
          title={`${p.name} - ${p.chain}`}
        />
      ))}
    </GoogleMap>
  );
}
