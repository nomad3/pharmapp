import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import client from "../api/client";
import useGeolocation from "../hooks/useGeolocation";
import PriceCard from "../components/PriceCard";
import PremiumGate from "../components/PremiumGate";
import PriceHistoryChart from "../components/charts/PriceHistoryChart";

export default function MedicationDetailPage() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { location } = useGeolocation();
  const [prices, setPrices] = useState([]);
  const [medication, setMedication] = useState(null);
  const [medId, setMedId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isPremium, setIsPremium] = useState(false);
  const [priceHistory, setPriceHistory] = useState([]);
  const [generics, setGenerics] = useState([]);
  const [alertPrice, setAlertPrice] = useState("");
  const [alertMsg, setAlertMsg] = useState("");
  const [cenabastCost, setCenabastCost] = useState(null);

  useEffect(() => {
    if (!slug) return;
    client.get(`/medications/${slug}`)
      .then(({ data }) => {
        setMedication(data);
        setMedId(data.id);
      })
      .catch((err) => console.error("Error fetching medication:", err));
  }, [slug]);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      client.get("/premium/status")
        .then(({ data }) => setIsPremium(data.tier === "premium"))
        .catch(() => {});
    }
  }, []);

  useEffect(() => {
    if (!location || !medId) return;
    const fetchData = async () => {
      try {
        const { data } = await client.get(`/prices/compare-transparent?medication_id=${medId}&lat=${location.lat}&lng=${location.lng}`);
        setPrices(data);
        if (data.length > 0 && data[0].cenabast_cost) {
          setCenabastCost(data[0].cenabast_cost);
        }
      } catch (err) {
        console.error("Error fetching prices:", err);
        try {
          const { data } = await client.get(`/prices/compare?medication_id=${medId}&lat=${location.lat}&lng=${location.lng}`);
          setPrices(data);
        } catch (err2) { console.error("Error fetching fallback prices:", err2); }
      }
      try {
        const { data } = await client.get(`/transparency/medication/${medId}/cenabast-cost`);
        if (data.avg_cenabast_cost) setCenabastCost(data.avg_cenabast_cost);
      } catch (err) { /* no transparency data */ }
      setLoading(false);
    };
    fetchData();
  }, [medId, location]);

  useEffect(() => {
    if (!isPremium || !medId) return;
    client.get(`/premium/price-history/${medId}`)
      .then(({ data }) => setPriceHistory(data))
      .catch(() => {});
    client.get(`/premium/generics/${medId}`)
      .then(({ data }) => setGenerics(data))
      .catch(() => {});
  }, [isPremium, medId]);

  const handleBuy = (priceItem) => {
    const token = localStorage.getItem("token");
    if (!token) { navigate("/login"); return; }
    const params = new URLSearchParams({
      pharmacy_id: priceItem.pharmacy.id,
      medication_id: medId,
      price_id: priceItem.price_id,
      price: priceItem.price,
      pharmacy_name: priceItem.pharmacy.name,
      medication_name: medication?.name || "",
      is_online: priceItem.is_online ? "true" : "false",
    });
    navigate(`/checkout?${params.toString()}`);
  };

  const handleSetAlert = async () => {
    if (!alertPrice) return;
    const token = localStorage.getItem("token");
    if (!token) { navigate("/login"); return; }
    try {
      await client.post("/premium/alerts", {
        medication_id: medId,
        target_price: parseFloat(alertPrice),
      });
      setAlertMsg("Alerta creada. Te avisaremos por WhatsApp.");
      setAlertPrice("");
    } catch (err) {
      setAlertMsg(err.response?.data?.detail || "Error al crear alerta");
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
      <Helmet>
        <title>{`${medication?.name || "Medicamento"} — Precios en farmacias | PharmApp`}</title>
        <meta name="description" content={`Compara precios de ${medication?.name || "medicamento"} en farmacias de Chile. ${prices.length} farmacias con stock.`} />
        <link rel="canonical" href={`https://pharmapp.cl/medicamento/${slug}`} />
        <meta property="og:title" content={`${medication?.name || "Medicamento"} — PharmApp`} />
        <meta property="og:description" content={`Compara precios de ${medication?.name || "medicamento"} en farmacias de Chile.`} />
        <meta property="og:type" content="product" />
        <meta property="og:locale" content="es_CL" />
        {medication && prices.length > 0 && (
          <script type="application/ld+json">
            {JSON.stringify({
              "@context": "https://schema.org",
              "@type": "Product",
              "name": medication.name,
              "description": `${medication.active_ingredient || ""} ${medication.dosage || ""} ${medication.form || ""}`.trim(),
              "offers": {
                "@type": "AggregateOffer",
                "priceCurrency": "CLP",
                "lowPrice": Math.round(prices[0]?.price),
                "highPrice": Math.round(prices[prices.length - 1]?.price),
                "offerCount": prices.length,
              },
            })}
          </script>
        )}
      </Helmet>
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

        {cenabastCost && prices.length > 0 && (
          <div className="transparency-banner">
            <div className="transparency-banner__icon">🏛️</div>
            <div className="transparency-banner__content">
              <div className="transparency-banner__title">Costo del Estado (Cenabast)</div>
              <div className="transparency-banner__cost">${Math.round(cenabastCost).toLocaleString("es-CL")} CLP</div>
              <div className="transparency-banner__desc">
                El Estado compra este medicamento por ${Math.round(cenabastCost).toLocaleString("es-CL")} CLP.
                {prices[0]?.price && (
                  <span> El precio más bajo en farmacias es <strong>${Math.round(prices[0].price).toLocaleString("es-CL")} CLP</strong>
                  {" "}({Math.round(((prices[0].price - cenabastCost) / cenabastCost) * 100)}% más caro).</span>
                )}
              </div>
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
                markupPct={item.markup_pct}
                isPrecioJusto={item.is_precio_justo}
                isOnline={item.is_online}
              />
            ))}
          </div>
        </div>

        {/* Premium: Price Alert */}
        <PremiumGate isPremium={isPremium} featureName="Alertas de precio">
          <div className="alert-section">
            <h3>🔔 Alerta de precio</h3>
            <p>Recibe un WhatsApp cuando el precio baje a tu objetivo.</p>
            <div className="alert-form">
              <input
                type="number"
                placeholder="Precio objetivo (CLP)"
                value={alertPrice}
                onChange={(e) => setAlertPrice(e.target.value)}
                className="input"
              />
              <button className="btn btn--primary btn--sm" onClick={handleSetAlert}>
                Crear alerta
              </button>
            </div>
            {alertMsg && <p className="alert-msg">{alertMsg}</p>}
          </div>
        </PremiumGate>

        {/* Premium: Price History */}
        <PremiumGate isPremium={isPremium} featureName="Historial de precios">
          <PriceHistoryChart data={priceHistory} title="Historial de precios" />
        </PremiumGate>

        {/* Premium: Generic Alternatives */}
        <PremiumGate isPremium={isPremium} featureName="Alternativas genéricas">
          <div className="generics-section">
            <h3>💊 Alternativas genéricas</h3>
            {generics.length === 0 ? (
              <p>No se encontraron alternativas genéricas.</p>
            ) : (
              <div className="generics-list">
                {generics.map((g) => (
                  <div key={g.id} className="generic-card" onClick={() => navigate(`/medicamento/${g.slug || g.id}`)}>
                    <div className="generic-card__name">{g.name}</div>
                    <div className="generic-card__meta">
                      {g.lab && <span>{g.lab}</span>}
                      {g.min_price && <span className="generic-price">desde ${Math.round(g.min_price).toLocaleString("es-CL")}</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </PremiumGate>
      </div>
    </div>
  );
}
