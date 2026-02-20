import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import client from "../api/client";
import useGeolocation from "../hooks/useGeolocation";
import PriceCard from "../components/PriceCard";

export default function MedicationDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { location } = useGeolocation();
  const [prices, setPrices] = useState([]);
  const [medication, setMedication] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!location) return;
    const fetchData = async () => {
      try {
        const { data } = await client.get(`/prices/compare?medication_id=${id}&lat=${location.lat}&lng=${location.lng}`);
        setPrices(data);
      } catch (err) { console.error("Error fetching prices:", err); }
      try {
        const { data } = await client.get("/medications/");
        const med = data.find(m => m.id === id);
        if (med) setMedication(med);
      } catch (err) { console.error("Error fetching medication:", err); }
      setLoading(false);
    };
    fetchData();
  }, [id, location]);

  const handleBuy = async (priceItem) => {
    const token = localStorage.getItem("token");
    if (!token) { navigate("/login"); return; }
    try {
      const { data } = await client.post("/orders", {
        pharmacy_id: priceItem.pharmacy.id,
        items: [{ medication_id: id, price_id: priceItem.pharmacy.id, quantity: 1 }],
        payment_provider: "mercadopago",
      });
      if (data.payment_url) window.location.href = data.payment_url;
    } catch (err) {
      console.error("Error creating order:", err);
    }
  };

  if (loading) {
    return (
      <div className="loading-state">
        <div className="spinner"></div>
        <p>Comparando precios...</p>
      </div>
    );
  }

  return (
    <div className="medication-detail">
      <div className="container">
        {medication && (
          <div className="med-detail-header">
            <h1>{medication.name}</h1>
            <div className="med-meta">
              {medication.active_ingredient && <span className="med-tag">{medication.active_ingredient}</span>}
              {medication.dosage && <span className="med-tag">{medication.dosage}</span>}
              {medication.form && <span className="med-tag">{medication.form}</span>}
              {medication.lab && <span className="med-tag">{medication.lab}</span>}
              {medication.requires_prescription && <span className="rx-badge">Requiere receta</span>}
            </div>
          </div>
        )}

        <div className="prices-section">
          <h2>
            📊 {prices.length} farmacia{prices.length !== 1 ? "s" : ""} con stock
          </h2>
          <div className="prices-list">
            {prices.map((item, i) => (
              <PriceCard
                key={i}
                price={item.price}
                pharmacy={item.pharmacy}
                distanceKm={item.distance_km}
                isBest={i === 0}
                onBuy={() => handleBuy(item)}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
