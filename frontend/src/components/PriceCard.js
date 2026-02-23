import React from "react";
import WhatsAppButton from "./WhatsAppButton";

const CHAIN_NAMES = {
  cruz_verde: "Cruz Verde",
  salcobrand: "Salcobrand",
  ahumada: "Ahumada",
  dr_simi: "Dr. Simi",
};

export default function PriceCard({ price, pharmacy, distanceKm, isBest, onBuy, markupPct, isPrecioJusto, isOnline }) {
  const markupColor = markupPct != null
    ? markupPct <= 100 ? "markup-low" : markupPct <= 300 ? "markup-medium" : "markup-high"
    : "";

  return (
    <div className={`price-card ${isBest ? "best-price" : ""} ${isOnline ? "online-pharmacy" : ""}`}>
      {isBest && <span className="best-badge">Mejor precio</span>}
      {isPrecioJusto && <span className="precio-justo-badge">Precio justo</span>}

      <div className={`chain-logo ${pharmacy.chain}`}>
        {(CHAIN_NAMES[pharmacy.chain] || pharmacy.chain).slice(0, 2).toUpperCase()}
      </div>

      <div className="price-info">
        <div className="pharmacy-name">{pharmacy.name}</div>
        <div className="pharmacy-address">{pharmacy.address}</div>
        {isOnline ? (
          <div className="distance online-badge">Despacho a domicilio</div>
        ) : distanceKm != null ? (
          <div className="distance">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
            {distanceKm.toFixed(1)} km
          </div>
        ) : null}
        {markupPct != null && (
          <div className={`markup-indicator ${markupColor}`}>
            +{Math.round(markupPct).toLocaleString("es-CL")}% sobre costo Cenabast
          </div>
        )}
      </div>

      <div className="price-amount">
        <div className="price">${price.toLocaleString("es-CL")}</div>
      </div>

      <div className="price-actions">
        <button className="btn btn--primary btn--sm buy-button" onClick={onBuy}>
          Comprar
        </button>
      </div>
    </div>
  );
}
