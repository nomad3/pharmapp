import React, { useEffect, useState, useRef, useCallback } from "react";
import { Helmet } from "react-helmet-async";
import client from "../../api/client";
import { AdminNav } from "./AdminDashboardPage";

const formatCLP = (n) => `$${Number(n).toLocaleString("es-CL")} CLP`;

export default function AdminUsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedUser, setSelectedUser] = useState(null);
  const [userDetail, setUserDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const debounceRef = useRef(null);

  const fetchUsers = useCallback((q) => {
    setLoading(true);
    const params = q ? `?search=${encodeURIComponent(q)}&limit=50` : "?limit=50";
    client
      .get(`/admin/users${params}`)
      .then(({ data }) => setUsers(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchUsers("");
  }, [fetchUsers]);

  const handleSearch = (value) => {
    setSearch(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      fetchUsers(value);
    }, 300);
  };

  const selectUser = (userId) => {
    if (selectedUser === userId) {
      setSelectedUser(null);
      setUserDetail(null);
      return;
    }
    setSelectedUser(userId);
    setDetailLoading(true);
    client
      .get(`/admin/users/${userId}`)
      .then(({ data }) => setUserDetail(data))
      .catch(console.error)
      .finally(() => setDetailLoading(false));
  };

  return (
    <div className="admin-page">
      <Helmet>
        <title>Usuarios Admin | Remedia</title>
        <meta name="robots" content="noindex" />
      </Helmet>
      <div className="container">
        <h1 className="page-title">Gestionar Usuarios</h1>
        <AdminNav />

        <div style={{ marginBottom: 20 }}>
          <input
            type="text"
            className="input"
            placeholder="Buscar por telefono o nombre..."
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
            style={{ minWidth: 300 }}
          />
        </div>

        {loading ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Cargando usuarios...</p>
          </div>
        ) : (
          <div className="data-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Telefono</th>
                  <th>Nombre</th>
                  <th>Pedidos</th>
                  <th>Total Gastado</th>
                  <th>Registro</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <React.Fragment key={u.id}>
                    <tr
                      className="clickable-row"
                      onClick={() => selectUser(u.id)}
                      style={{
                        background:
                          selectedUser === u.id
                            ? "var(--primary-light)"
                            : undefined,
                      }}
                    >
                      <td>{u.phone || "-"}</td>
                      <td>{u.name || "-"}</td>
                      <td>{u.order_count ?? 0}</td>
                      <td>{formatCLP(u.total_spent ?? 0)}</td>
                      <td>
                        {u.created_at
                          ? new Date(u.created_at).toLocaleDateString("es-CL", {
                              day: "numeric",
                              month: "short",
                              year: "numeric",
                            })
                          : "-"}
                      </td>
                    </tr>
                    {selectedUser === u.id && (
                      <tr>
                        <td colSpan={5} style={{ background: "var(--bg)" }}>
                          {detailLoading ? (
                            <div
                              style={{
                                padding: 24,
                                textAlign: "center",
                              }}
                            >
                              <div className="spinner" style={{ margin: "0 auto 8px" }}></div>
                              <p style={{ fontSize: 14, color: "var(--text-secondary)" }}>
                                Cargando detalle...
                              </p>
                            </div>
                          ) : userDetail ? (
                            <div style={{ padding: "16px 8px" }}>
                              <div style={{ marginBottom: 16 }}>
                                <strong>Informacion del usuario</strong>
                                <p style={{ fontSize: 14, color: "var(--text-secondary)", marginTop: 4 }}>
                                  Tel: {userDetail.phone || "-"} | Nombre:{" "}
                                  {userDetail.name || "-"} | Email:{" "}
                                  {userDetail.email || "-"}
                                </p>
                              </div>
                              <strong>Historial de pedidos</strong>
                              {userDetail.orders && userDetail.orders.length > 0 ? (
                                <table
                                  className="admin-table"
                                  style={{ marginTop: 8 }}
                                >
                                  <thead>
                                    <tr>
                                      <th>ID</th>
                                      <th>Estado</th>
                                      <th>Total</th>
                                      <th>Fecha</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {userDetail.orders.map((o) => (
                                      <tr key={o.id}>
                                        <td>
                                          <code>{o.id.slice(0, 8)}</code>
                                        </td>
                                        <td>
                                          <span
                                            className={`status-badge status-${o.status}`}
                                          >
                                            {o.status}
                                          </span>
                                        </td>
                                        <td>{formatCLP(o.total)}</td>
                                        <td>
                                          {new Date(
                                            o.created_at
                                          ).toLocaleDateString("es-CL", {
                                            day: "numeric",
                                            month: "short",
                                          })}
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              ) : (
                                <p
                                  style={{
                                    color: "var(--text-secondary)",
                                    marginTop: 8,
                                    fontSize: 14,
                                  }}
                                >
                                  Sin pedidos
                                </p>
                              )}
                            </div>
                          ) : (
                            <p
                              style={{
                                padding: 24,
                                textAlign: "center",
                                color: "var(--text-secondary)",
                              }}
                            >
                              No se pudo cargar el detalle
                            </p>
                          )}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
                {users.length === 0 && (
                  <tr>
                    <td
                      colSpan={5}
                      style={{ textAlign: "center", padding: 24 }}
                    >
                      No se encontraron usuarios
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
