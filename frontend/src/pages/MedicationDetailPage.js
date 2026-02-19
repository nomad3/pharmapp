import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import client from "../api/client";
import useGeolocation from "../hooks/useGeolocation";
import PriceCard from "../components/PriceCard";
import WhatsAppButton from "../components/WhatsAppButton";

export default function MedicationDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { location } = useGeolocation();
  const [prices, setPrices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!location) return;
    client.get(`/prices/compare?medication_id=${id}&lat=${location.lat}&lng=${location.lng}`)
      .then(({ data }) => setPrices(data))
      .catch(console.error)
      .finally(() => setLoading(false));
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

  if (loading) return <p>Comparando precios...</p>;

  return (
    <div className="medication-detail">
      <h2>Comparación de precios</h2>
      {prices.map((item, i) => (
        <div key={i}>
          <PriceCard price={item.price} pharmacy={item.pharmacy} distanceKm={item.distance_km} />
          <WhatsAppButton onClick={() => handleBuy(item)} />
        </div>
      ))}
    </div>
  );
}
