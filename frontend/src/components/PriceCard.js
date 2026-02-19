import React from "react";

export default function PriceCard({ price, pharmacy, distanceKm }) {
  return (
    <div className="price-card">
      <div className="price-card-header">
        <span className="pharmacy-chain">{pharmacy.chain}</span>
        <span className="price">${price.toLocaleString("es-CL")}</span>
      </div>
      <p className="pharmacy-name">{pharmacy.name}</p>
      <p className="pharmacy-address">{pharmacy.address}</p>
      {distanceKm && <p className="distance">{distanceKm} km</p>}
    </div>
  );
}
