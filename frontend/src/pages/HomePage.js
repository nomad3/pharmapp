import React from "react";
import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import SearchBar from "../components/SearchBar";
import useGeolocation from "../hooks/useGeolocation";

const CATEGORIES = [
  { icon: "💊", name: "Analgésicos", query: "paracetamol", desc: "Dolor y fiebre" },
  { icon: "🦠", name: "Antibióticos", query: "amoxicilina", desc: "Infecciones" },
  { icon: "❤️", name: "Cardiovascular", query: "losartan", desc: "Presión e hipertensión" },
  { icon: "🫁", name: "Digestivo", query: "omeprazol", desc: "Estómago y reflujo" },
];

export default function HomePage() {
  const { location, error, loading } = useGeolocation();

  return (
    <div className="home-page">
      <Helmet>
        <title>Remedia — Compara precios de medicamentos en Chile</title>
        <meta name="description" content="Compara precios de medicamentos en farmacias de Chile. Encuentra el mejor precio cerca de ti y compra por WhatsApp." />
      </Helmet>
      <section className="home-hero">
        <div className="container">
          <h1>Compara precios de medicamentos</h1>
          <p className="subtitle">
            Encuentra el mejor precio en farmacias cerca de ti y compra por WhatsApp
          </p>
          <SearchBar />
          <div className={`geo-status ${loading ? "loading" : error ? "error" : ""}`}>
            <span className="dot"></span>
            {loading && <span>Detectando ubicación...</span>}
            {error && <span>Ubicación no disponible</span>}
            {location && <span>Ubicación detectada — buscando farmacias cercanas</span>}
          </div>
        </div>
      </section>

      <div className="container">
        <div className="home-stats">
          <div className="stat-item">
            <div className="stat-number">4</div>
            <div className="stat-label">Cadenas</div>
          </div>
          <div className="stat-item">
            <div className="stat-number">5K+</div>
            <div className="stat-label">Medicamentos</div>
          </div>
          <div className="stat-item">
            <div className="stat-number">50%</div>
            <div className="stat-label">Ahorro promedio</div>
          </div>
          <div className="stat-item">
            <div className="stat-number">24/7</div>
            <div className="stat-label">WhatsApp</div>
          </div>
        </div>
      </div>

      <section className="home-categories">
        <div className="container">
          <h2 className="section-title">Categorías populares</h2>
          <p className="section-subtitle">Busca por tipo de medicamento</p>
          <div className="category-grid">
            {CATEGORIES.map((cat) => (
              <Link to={`/search?q=${cat.query}`} className="category-card" key={cat.name}>
                <div className="category-icon">{cat.icon}</div>
                <h3>{cat.name}</h3>
                <p>{cat.desc}</p>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="home-how">
        <div className="container">
          <h2 className="section-title">Cómo funciona</h2>
          <p className="section-subtitle">Encuentra tu medicamento en 3 pasos</p>
          <div className="how-steps">
            <div className="how-step">
              <div className="step-icon">🔍</div>
              <h3>1. Busca tu medicamento</h3>
              <p>Escribe el nombre o principio activo del medicamento que necesitas</p>
            </div>
            <div className="how-step">
              <div className="step-icon">📊</div>
              <h3>2. Compara precios</h3>
              <p>Ve los precios en farmacias cercanas ordenados del más barato al más caro</p>
            </div>
            <div className="how-step">
              <div className="step-icon">📱</div>
              <h3>3. Compra por WhatsApp</h3>
              <p>Un agente coordina tu pago, delivery y seguimiento del pedido</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
