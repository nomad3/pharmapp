import React, { useEffect, useState } from "react";
import { Helmet } from "react-helmet-async";
import client from "../../api/client";
import { AdminNav } from "./AdminDashboardPage";

export default function AdminSettingsPage() {
  const [form, setForm] = useState({
    bank_name: "", bank_account_type: "", bank_account_number: "",
    bank_rut: "", bank_holder_name: "", bank_email: "",
  });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    client.get("/settings/bank-details")
      .then(({ data }) => setForm(prev => ({ ...prev, ...data })))
      .catch(() => {});
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setMessage("");
    try {
      await client.put("/settings/bank-details", form);
      setMessage("Guardado correctamente");
    } catch {
      setMessage("Error al guardar");
    }
    setSaving(false);
  };

  const fields = [
    { key: "bank_name", label: "Nombre del banco", placeholder: "Ej: Banco Estado" },
    { key: "bank_account_type", label: "Tipo de cuenta", placeholder: "Ej: Cuenta Corriente" },
    { key: "bank_account_number", label: "Numero de cuenta", placeholder: "Ej: 123456789" },
    { key: "bank_rut", label: "RUT", placeholder: "Ej: 76.123.456-7" },
    { key: "bank_holder_name", label: "Nombre del titular", placeholder: "Ej: Remedia SpA" },
    { key: "bank_email", label: "Email de notificacion", placeholder: "Ej: pagos@remedia.cl" },
  ];

  return (
    <div className="admin-page">
      <Helmet>
        <title>{`Configuracion Admin | Remedia`}</title>
        <meta name="robots" content="noindex" />
      </Helmet>
      <div className="container">
        <h1 className="page-title">Configuracion</h1>
        <AdminNav />

        <div className="admin-settings-section">
          <h2>Datos Bancarios para Transferencia</h2>
          <p style={{ color: "var(--text-secondary)", marginBottom: 16 }}>
            Estos datos se muestran al usuario cuando elige pagar por transferencia bancaria.
          </p>
          {fields.map(f => (
            <div key={f.key} className="form-group">
              <label className="form-label">{f.label}</label>
              <input
                className="input"
                type="text"
                placeholder={f.placeholder}
                value={form[f.key]}
                onChange={e => setForm(prev => ({ ...prev, [f.key]: e.target.value }))}
              />
            </div>
          ))}
          {message && (
            <div className={`checkout-${message.includes("Error") ? "error" : "success"}`} style={{ marginBottom: 12 }}>
              {message}
            </div>
          )}
          <button className="btn btn--primary" onClick={handleSave} disabled={saving}>
            {saving ? "Guardando..." : "Guardar datos bancarios"}
          </button>
        </div>
      </div>
    </div>
  );
}
