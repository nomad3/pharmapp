import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import client from "../api/client";

const FEATURES = [
  {
    icon: "🔔",
    title: "Alertas de precio",
    desc: "Recibe notificaciones por WhatsApp cuando el precio de tu medicamento baje al nivel que quieres.",
  },
  {
    icon: "📈",
    title: "Historial de precios",
    desc: "Visualiza la evolución de precios en el tiempo para tomar mejores decisiones de compra.",
  },
  {
    icon: "💊",
    title: "Alternativas genéricas",
    desc: "Encuentra opciones genéricas más baratas con el mismo principio activo.",
  },
  {
    icon: "📋",
    title: "Gestión de recetas",
    desc: "Sube fotos de tus recetas y vincula medicamentos para un acceso rápido.",
  },
];

export default function PremiumPage() {
  const navigate = useNavigate();
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [checkingOut, setCheckingOut] = useState(false);
  const token = localStorage.getItem("token");

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    client.get("/premium/status")
      .then(({ data }) => setStatus(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [token]);

  const handleSubscribe = async () => {
    if (!token) {
      navigate("/login");
      return;
    }
    setCheckingOut(true);
    try {
      const { data } = await client.post("/premium/checkout", {});
      window.location.href = data.checkout_url;
    } catch (err) {
      alert("Error al iniciar checkout");
      setCheckingOut(false);
    }
  };

  const isPremium = status?.tier === "premium";

  return (
    <div className="premium-page">
      <div className="container">
        <div className="premium-hero">
          <h1>PharmApp Premium</h1>
          <p className="premium-subtitle">
            Aprovecha al máximo PharmApp con funciones exclusivas para ahorrar más en tus medicamentos.
          </p>
          <div className="premium-price">
            <span className="price-amount">$2.990</span>
            <span className="price-period">CLP/mes</span>
          </div>
          {isPremium ? (
            <div className="premium-active-badge">
              Premium activo
              {status.current_period_end && (
                <span> — hasta {status.current_period_end.slice(0, 10)}</span>
              )}
            </div>
          ) : (
            <button className="btn btn--primary btn--lg" onClick={handleSubscribe} disabled={checkingOut || loading}>
              {checkingOut ? "Redirigiendo a pago..." : "Activar Premium"}
            </button>
          )}
        </div>

        <div className="premium-features">
          {FEATURES.map((f, i) => (
            <div key={i} className="premium-feature-card">
              <div className="feature-icon">{f.icon}</div>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
