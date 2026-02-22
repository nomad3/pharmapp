import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import client from "../api/client";

const TIERS = [
  {
    name: "Free",
    price: "$0",
    period: "para siempre",
    features: [
      "100 requests/día",
      "10 requests/min",
      "Acceso a datos básicos",
      "1 API key",
    ],
    cta: "Comenzar gratis",
    tier: "free",
    highlight: false,
  },
  {
    name: "Pro",
    price: "$500",
    period: "USD/mes",
    features: [
      "10,000 requests/día",
      "100 requests/min",
      "Todos los endpoints",
      "Export CSV",
      "API keys ilimitadas",
      "Soporte email",
    ],
    cta: "Suscribirse a Pro",
    tier: "pro",
    highlight: true,
  },
  {
    name: "Enterprise",
    price: "$5,000",
    period: "USD/mes",
    features: [
      "Requests ilimitados",
      "1,000 requests/min",
      "Todos los endpoints",
      "Export CSV + bulk",
      "API keys ilimitadas",
      "Dashboard analytics",
      "Soporte prioritario",
      "SLA 99.9%",
    ],
    cta: "Suscribirse a Enterprise",
    tier: "enterprise",
    highlight: false,
  },
];

export default function PricingPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(null);
  const token = localStorage.getItem("token");

  const handleSubscribe = async (tier) => {
    if (!token) {
      navigate("/login");
      return;
    }
    if (tier === "free") {
      navigate("/org/new");
      return;
    }

    setLoading(tier);
    try {
      const orgSlug = localStorage.getItem("org_slug");
      if (!orgSlug) {
        navigate("/org/new");
        return;
      }
      const { data } = await client.post("/billing/checkout", {
        tier,
        org_slug: orgSlug,
      });
      window.location.href = data.checkout_url;
    } catch (err) {
      console.error("Checkout error:", err);
      alert("Error al iniciar el checkout. Crea una organización primero.");
    }
    setLoading(null);
  };

  return (
    <div className="pricing-page">
      <div className="container">
        <div className="pricing-header">
          <h1>API de Datos Farmacéuticos</h1>
          <p className="pricing-subtitle">
            Acceso programático a inteligencia de mercado farmacéutico chileno.
            Precios, market share, tendencias y datos de procurement.
          </p>
        </div>

        <div className="pricing-grid">
          {TIERS.map((t) => (
            <div key={t.tier} className={`pricing-card ${t.highlight ? "pricing-card--highlight" : ""}`}>
              {t.highlight && <div className="pricing-badge">Más popular</div>}
              <h2 className="pricing-card__name">{t.name}</h2>
              <div className="pricing-card__price">
                <span className="price-amount">{t.price}</span>
                <span className="price-period">{t.period}</span>
              </div>
              <ul className="pricing-card__features">
                {t.features.map((f, i) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
              <button
                className={`pricing-card__cta ${t.highlight ? "cta--primary" : "cta--secondary"}`}
                onClick={() => handleSubscribe(t.tier)}
                disabled={loading === t.tier}
              >
                {loading === t.tier ? "Cargando..." : t.cta}
              </button>
            </div>
          ))}
        </div>

        <div className="pricing-faq">
          <h2>Datos disponibles</h2>
          <div className="faq-grid">
            <div className="faq-item">
              <h3>Precios de mercado</h3>
              <p>129K+ precios de Cruz Verde, Salcobrand, Ahumada y Dr. Simi actualizados regularmente</p>
            </div>
            <div className="faq-item">
              <h3>Market share</h3>
              <p>Análisis de participación de mercado por principio activo y segmento terapéutico</p>
            </div>
            <div className="faq-item">
              <h3>Procurement público</h3>
              <p>680K+ facturas Cenabast, órdenes de compra y adjudicaciones del sector público</p>
            </div>
            <div className="faq-item">
              <h3>Tendencias</h3>
              <p>Series temporales de ventas, precios y distribución por región y producto</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
