import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import OrgSidebar from "../components/OrgSidebar";
import useOrg from "../hooks/useOrg";

export default function OrgSettingsPage() {
  const { slug } = useParams();
  const { org, members, loading, loadMembers, inviteMember, removeMember } = useOrg(slug);
  const [phone, setPhone] = useState("");
  const [role, setRole] = useState("viewer");
  const [inviting, setInviting] = useState(false);

  useEffect(() => {
    loadMembers();
  }, [loadMembers]);

  const handleInvite = async (e) => {
    e.preventDefault();
    if (!phone) return;
    setInviting(true);
    try {
      await inviteMember(phone, role);
      setPhone("");
      setRole("viewer");
    } catch (err) {
      alert(err.response?.data?.detail || "Error al invitar");
    }
    setInviting(false);
  };

  if (loading) {
    return (
      <div className="loading-state">
        <div className="spinner"></div>
        <p>Cargando...</p>
      </div>
    );
  }

  return (
    <div className="org-page">
      <OrgSidebar slug={slug} />
      <div className="org-content">
        <div className="container">
          <h1 className="page-title">Configuración — {org?.name}</h1>

          <section className="settings-section">
            <h2>Miembros</h2>

            <form className="invite-form" onSubmit={handleInvite}>
              <input
                type="tel"
                placeholder="+56912345678"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="input"
              />
              <select value={role} onChange={(e) => setRole(e.target.value)} className="select">
                <option value="viewer">Viewer</option>
                <option value="analyst">Analyst</option>
                <option value="admin">Admin</option>
              </select>
              <button type="submit" className="btn btn--primary" disabled={inviting}>
                {inviting ? "Invitando..." : "Invitar"}
              </button>
            </form>

            <div className="data-table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Teléfono</th>
                    <th>Nombre</th>
                    <th>Rol</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {members.map((m) => (
                    <tr key={m.id}>
                      <td>{m.user_phone || "—"}</td>
                      <td>{m.user_name || "—"}</td>
                      <td><span className={`role-badge role--${m.role}`}>{m.role}</span></td>
                      <td>
                        {m.role !== "owner" && (
                          <button className="btn btn--sm btn--danger" onClick={() => removeMember(m.user_id)}>
                            Eliminar
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
