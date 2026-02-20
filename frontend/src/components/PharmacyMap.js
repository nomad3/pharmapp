import React from "react";
import { GoogleMap, Marker, useJsApiLoader } from "@react-google-maps/api";

const containerStyle = { width: "100%", height: "500px" };

const mapOptions = {
  disableDefaultUI: false,
  zoomControl: true,
  streetViewControl: false,
  mapTypeControl: false,
  fullscreenControl: true,
  styles: [
    { featureType: "poi.business", stylers: [{ visibility: "off" }] },
    { featureType: "poi.park", elementType: "labels.text", stylers: [{ visibility: "off" }] },
  ],
};

export default function PharmacyMap({ center, pharmacies }) {
  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: process.env.REACT_APP_GOOGLE_MAPS_API_KEY || "",
  });

  if (!isLoaded) {
    return (
      <div style={{ width: "100%", height: "500px", display: "flex", alignItems: "center", justifyContent: "center", background: "#f0f0f0" }}>
        <p>Cargando mapa...</p>
      </div>
    );
  }

  return (
    <GoogleMap mapContainerStyle={containerStyle} center={center} zoom={14} options={mapOptions}>
      {pharmacies.map((p) => (
        <Marker
          key={p.id}
          position={{ lat: p.lat || center.lat, lng: p.lng || center.lng }}
          title={`${p.name} - ${p.chain}`}
        />
      ))}
    </GoogleMap>
  );
}
