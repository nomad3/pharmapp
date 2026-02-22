import React from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import SearchBar from "./SearchBar";

export default function Layout({ children }) {
  const navigate = useNavigate();
  const location = useLocation();
  const token = localStorage.getItem("token");
  const orgSlug = localStorage.getItem("org_slug");
  const isHome = location.pathname === "/";

  return (
    <div className="layout">
      <header className="header">
        <div className="header-inner container">
          <Link to="/" className="logo">
            <span className="logo-icon">+</span>
            <span className="logo-text">PharmApp</span>
          </Link>

          {!isHome && (
            <div className="header-search">
              <SearchBar compact />
            </div>
          )}

          <nav className="header-nav">
            <Link to="/analytics" className={`nav-link ${location.pathname === "/analytics" ? "active" : ""}`}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20v-6"/></svg>
              <span>Analytics</span>
            </Link>
            <Link to="/pricing" className={`nav-link ${location.pathname === "/pricing" ? "active" : ""}`}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
              <span>API</span>
            </Link>
            <Link to="/map" className={`nav-link ${location.pathname === "/map" ? "active" : ""}`}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
              <span>Farmacias</span>
            </Link>
            <Link to="/favorites" className={`nav-link ${location.pathname === "/favorites" ? "active" : ""}`}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
              <span>Favoritos</span>
            </Link>
            <Link to="/orders" className={`nav-link ${location.pathname === "/orders" ? "active" : ""}`}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>
              <span>Pedidos</span>
            </Link>
            {orgSlug && (
              <Link to={`/org/${orgSlug}`} className={`nav-link ${location.pathname.startsWith("/org/") ? "active" : ""}`}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                <span>Org</span>
              </Link>
            )}
            {token ? (
              <button className="nav-link nav-btn" onClick={() => { localStorage.removeItem("token"); localStorage.removeItem("user"); localStorage.removeItem("org_slug"); localStorage.removeItem("org_id"); navigate("/"); }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
                <span>Salir</span>
              </button>
            ) : (
              <Link to="/login" className={`nav-link nav-login ${location.pathname === "/login" ? "active" : ""}`}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                <span>Ingresar</span>
              </Link>
            )}
          </nav>
        </div>
      </header>

      <main className="main-content">
        {children}
      </main>

      <footer className="footer">
        <div className="footer-inner container">
          <div className="footer-brand">
            <span className="logo-icon">+</span>
            <span className="logo-text">PharmApp</span>
            <p>Encuentra los medicamentos más baratos cerca de ti</p>
          </div>
          <div className="footer-links">
            <div className="footer-col">
              <h4>Explorar</h4>
              <Link to="/">Inicio</Link>
              <Link to="/map">Mapa de farmacias</Link>
              <Link to="/favorites">Mis favoritos</Link>
            </div>
            <div className="footer-col">
              <h4>Cuenta</h4>
              <Link to="/login">Iniciar sesión</Link>
              <Link to="/orders">Mis pedidos</Link>
              <Link to="/premium">Premium</Link>
            </div>
            <div className="footer-col">
              <h4>Empresas</h4>
              <Link to="/pricing">API de datos</Link>
              <Link to="/analytics">Market intelligence</Link>
            </div>
          </div>
          <div className="footer-bottom">
            <p>&copy; 2026 PharmApp. Todos los derechos reservados.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
