import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import client from "../api/client";

export default function ProfilePage() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [name, setName] = useState("");
  const [comuna, setComuna] = useState("");
  const [prefs, setPrefs] = useState({
    order_updates: true,
    price_alerts: true,
    refill_reminders: true,
    promotions: false,
  });
  const [addresses, setAddresses] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newAddress, setNewAddress] = useState({ label: "home", address: "", comuna: "", instructions: "" });
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      navigate("/login");
      return;
    }
    loadProfile();
    loadAddresses();
  }, [navigate]);

  async function loadProfile() {
    try {
      const { data } = await client.get("/auth/profile");
      setProfile(data);
      setName(data.name || "");
      setComuna(data.comuna || "");
      if (data.notification_prefs) {
        setPrefs(data.notification_prefs);
      }
    } catch (err) {
      if (err.response?.status === 401) {
        navigate("/login");
      }
    } finally {
      setLoading(false);
    }
  }

  async function loadAddresses() {
    try {
      const { data } = await client.get("/addresses/");
      setAddresses(data);
    } catch {
      // ignore
    }
  }

  async function handleSave() {
    setSaving(true);
    setSuccess(false);
    try {
      await client.put("/auth/profile", {
        name,
        comuna,
        notification_prefs: prefs,
      });
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch {
      // ignore
    } finally {
      setSaving(false);
    }
  }

  async function handleAddAddress(e) {
    e.preventDefault();
    try {
      await client.post("/addresses/", newAddress);
      setNewAddress({ label: "home", address: "", comuna: "", instructions: "" });
      setShowAddForm(false);
      loadAddresses();
    } catch {
      // ignore
    }
  }

  async function handleDeleteAddress(id) {
    if (!window.confirm("Eliminar esta direccion?")) return;
    try {
      await client.delete(`/addresses/${id}`);
      setAddresses(addresses.filter((a) => a.id !== id));
    } catch {
      // ignore
    }
  }

  function togglePref(key) {
    setPrefs((p) => ({ ...p, [key]: !p[key] }));
  }

  function handleLogout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    localStorage.removeItem("org_slug");
    localStorage.removeItem("org_id");
    navigate("/");
  }

  if (loading) {
    return (
      <div className="profile-page">
        <p style={{ textAlign: "center", padding: 40, color: "var(--text-secondary)" }}>Cargando perfil...</p>
      </div>
    );
  }

  return (
    <div className="profile-page">
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 20, color: "var(--text)" }}>Mi Perfil</h1>

      {/* Personal Info */}
      <div className="profile-section">
        <h2>Informacion Personal</h2>
        <div className="profile-field">
          <label>Telefono</label>
          <input type="text" value={profile?.phone_number || ""} disabled />
        </div>
        <div className="profile-field">
          <label>Nombre</label>
          <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Tu nombre" />
        </div>
        <div className="profile-field">
          <label>Comuna</label>
          <input type="text" value={comuna} onChange={(e) => setComuna(e.target.value)} placeholder="Tu comuna" />
        </div>
      </div>

      {/* Delivery Addresses */}
      <div className="profile-section">
        <h2>Direcciones de Entrega</h2>
        {addresses.length === 0 && !showAddForm && (
          <p style={{ fontSize: 14, color: "var(--text-secondary)", marginBottom: 12 }}>No tienes direcciones guardadas.</p>
        )}
        {addresses.map((addr) => (
          <div key={addr.id} className="address-card">
            <div className="address-card-info">
              <span>{addr.address}</span>
              <small>{addr.comuna}{addr.instructions ? ` - ${addr.instructions}` : ""}</small>
            </div>
            <button className="address-delete-btn" onClick={() => handleDeleteAddress(addr.id)} title="Eliminar">
              &#10005;
            </button>
          </div>
        ))}
        {showAddForm ? (
          <form className="add-address-form" onSubmit={handleAddAddress}>
            <input
              type="text"
              placeholder="Direccion"
              value={newAddress.address}
              onChange={(e) => setNewAddress({ ...newAddress, address: e.target.value })}
              required
            />
            <input
              type="text"
              placeholder="Comuna"
              value={newAddress.comuna}
              onChange={(e) => setNewAddress({ ...newAddress, comuna: e.target.value })}
              required
            />
            <input
              type="text"
              placeholder="Referencia (opcional)"
              value={newAddress.instructions}
              onChange={(e) => setNewAddress({ ...newAddress, instructions: e.target.value })}
              style={{ gridColumn: "1 / -1" }}
            />
            <div style={{ gridColumn: "1 / -1", display: "flex", gap: 8 }}>
              <button type="submit" className="profile-save-btn" style={{ flex: 1 }}>Agregar</button>
              <button type="button" className="profile-logout-btn" style={{ flex: 1 }} onClick={() => setShowAddForm(false)}>Cancelar</button>
            </div>
          </form>
        ) : (
          <button
            className="profile-save-btn"
            style={{ marginTop: 8 }}
            onClick={() => setShowAddForm(true)}
          >
            + Agregar direccion
          </button>
        )}
      </div>

      {/* Notification Preferences */}
      <div className="profile-section">
        <h2>Notificaciones</h2>
        <label className="toggle-row">
          <span>Actualizaciones de pedido</span>
          <input type="checkbox" checked={prefs.order_updates} onChange={() => togglePref("order_updates")} />
          <span className="toggle-switch"></span>
        </label>
        <label className="toggle-row">
          <span>Alertas de precio</span>
          <input type="checkbox" checked={prefs.price_alerts} onChange={() => togglePref("price_alerts")} />
          <span className="toggle-switch"></span>
        </label>
        <label className="toggle-row">
          <span>Recordatorios de recarga</span>
          <input type="checkbox" checked={prefs.refill_reminders} onChange={() => togglePref("refill_reminders")} />
          <span className="toggle-switch"></span>
        </label>
        <label className="toggle-row">
          <span>Promociones</span>
          <input type="checkbox" checked={prefs.promotions} onChange={() => togglePref("promotions")} />
          <span className="toggle-switch"></span>
        </label>
      </div>

      {/* Save */}
      <button className="profile-save-btn" onClick={handleSave} disabled={saving}>
        {saving ? "Guardando..." : "Guardar"}
      </button>
      {success && <p className="profile-success">Perfil actualizado</p>}

      {/* Account */}
      <div className="profile-section" style={{ marginTop: 20 }}>
        <h2>Cuenta</h2>
        <button className="profile-logout-btn" onClick={handleLogout}>Cerrar sesion</button>
      </div>
    </div>
  );
}
