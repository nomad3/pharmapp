import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import client from "../api/client";
import OrgSidebar from "../components/OrgSidebar";
import UsageChart from "../components/UsageChart";

export default function ApiKeysPage() {
  const { slug } = useParams();
  const [keys, setKeys] = useState([]);
  const [name, setName] = useState("");
  const [creating, setCreating] = useState(false);
  const [newKey, setNewKey] = useState(null);
  const [usage, setUsage] = useState(null);
  const [selectedKeyId, setSelectedKeyId] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadKeys();
  }, [slug]); // eslint-disable-line react-hooks/exhaustive-deps

  async function loadKeys() {
    setLoading(true);
    try {
      const { data } = await client.get(`/api-keys/?org_slug=${slug}`);
      setKeys(data);
    } catch (e) {
      console.error("Failed to load keys", e);
    }
    setLoading(false);
  }

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!name) return;
    setCreating(true);
    try {
      const { data } = await client.post("/api-keys/", { name, org_slug: slug });
      setNewKey(data.key);
      setName("");
      loadKeys();
    } catch (err) {
      alert(err.response?.data?.detail || "Error al crear key");
    }
    setCreating(false);
  };

  const handleRevoke = async (keyId) => {
    if (!window.confirm("Revocar esta API key?")) return;
    try {
      await client.delete(`/api-keys/${keyId}`);
      loadKeys();
    } catch (e) {
      console.error("Failed to revoke key", e);
    }
  };

  const handleViewUsage = async (keyId) => {
    setSelectedKeyId(keyId);
    try {
      const { data } = await client.get(`/api-keys/${keyId}/usage`);
      setUsage(data);
    } catch (e) {
      console.error("Failed to load usage", e);
    }
  };

  if (loading) {
    return (
      <div className="loading-state">
        <div className="spinner"></div>
        <p>Cargando API keys...</p>
      </div>
    );
  }

  return (
    <div className="org-page">
      <OrgSidebar slug={slug} />
      <div className="org-content">
        <div className="container">
          <h1 className="page-title">API Keys</h1>

          <form className="key-create-form" onSubmit={handleCreate}>
            <input
              type="text"
              placeholder="Nombre de la key (ej: producción, staging)"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="input"
            />
            <button type="submit" className="btn btn--primary" disabled={creating}>
              {creating ? "Creando..." : "Crear API Key"}
            </button>
          </form>

          {newKey && (
            <div className="key-created-alert">
              <p><strong>API Key creada. Copia este valor ahora — no se mostrará de nuevo:</strong></p>
              <code className="key-value">{newKey}</code>
              <button className="btn btn--sm btn--secondary" onClick={() => { navigator.clipboard.writeText(newKey); }}>
                Copiar
              </button>
              <button className="btn btn--sm" onClick={() => setNewKey(null)}>Cerrar</button>
            </div>
          )}

          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Prefijo</th>
                  <th>Estado</th>
                  <th>Creada</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {keys.map((k) => (
                  <tr key={k.id}>
                    <td>{k.name}</td>
                    <td><code>pa_live_{k.key_prefix}...</code></td>
                    <td>
                      <span className={`status-badge status--${k.is_active ? "active" : "revoked"}`}>
                        {k.is_active ? "Activa" : "Revocada"}
                      </span>
                    </td>
                    <td>{k.created_at ? k.created_at.slice(0, 10) : "—"}</td>
                    <td className="key-actions">
                      <button className="btn btn--sm btn--secondary" onClick={() => handleViewUsage(k.id)}>
                        Uso
                      </button>
                      {k.is_active && (
                        <button className="btn btn--sm btn--danger" onClick={() => handleRevoke(k.id)}>
                          Revocar
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {usage && selectedKeyId && (
            <div className="usage-detail">
              <h2>Uso de API Key</h2>
              <div className="usage-stats">
                <div className="stat-card">
                  <div className="stat-card__value">{usage.total_requests.toLocaleString()}</div>
                  <div className="stat-card__label">Total requests</div>
                </div>
                <div className="stat-card">
                  <div className="stat-card__value">{usage.requests_today.toLocaleString()}</div>
                  <div className="stat-card__label">Requests hoy</div>
                </div>
                <div className="stat-card">
                  <div className="stat-card__value">{usage.avg_response_time_ms}ms</div>
                  <div className="stat-card__label">Tiempo promedio</div>
                </div>
              </div>
              <UsageChart data={usage.top_endpoints} title="Top endpoints" />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
