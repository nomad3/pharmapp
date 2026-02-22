import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import client from "../api/client";
import OrgSidebar from "../components/OrgSidebar";

export default function AdherenceSponsorPage() {
  const { slug } = useParams();
  const [activeTab, setActiveTab] = useState("programs");
  const [programs, setPrograms] = useState([]);
  const [charges, setCharges] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [progRes, chargeRes] = await Promise.all([
          client.get("/adherence/sponsor/programs").catch(() => ({ data: [] })),
          client.get("/adherence/sponsor/charges").catch(() => ({ data: [] })),
        ]);
        setPrograms(progRes.data);
        setCharges(chargeRes.data);
      } catch (err) {
        console.error("Error loading sponsor data:", err);
      }
      setLoading(false);
    };
    fetchData();
  }, []);

  const tabs = [
    { id: "programs", label: "Programas" },
    { id: "charges", label: "Cargos" },
  ];

  if (loading) {
    return <div className="loading-state"><div className="spinner"></div></div>;
  }

  return (
    <div className="org-layout container">
      {slug && <OrgSidebar slug={slug} />}
      <div className="org-main">
        <h1>Sponsor Dashboard</h1>

        <div className="tab-nav">
          {tabs.map((tab) => (
            <button key={tab.id} className={`tab-btn ${activeTab === tab.id ? "active" : ""}`} onClick={() => setActiveTab(tab.id)}>
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab === "programs" && (
          <section>
            <h2>Programas Patrocinados</h2>
            {programs.length === 0 ? (
              <p className="empty-state">No hay programas patrocinados.</p>
            ) : (
              <div className="data-table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Programa</th>
                      <th>Presupuesto Total</th>
                      <th>Restante</th>
                      <th>Costo/Enrollment</th>
                      <th>Costo/Refill</th>
                    </tr>
                  </thead>
                  <tbody>
                    {programs.map((p) => (
                      <tr key={p.id}>
                        <td>{p.program_id.slice(0, 8)}</td>
                        <td>${Math.round(p.budget_total).toLocaleString("es-CL")}</td>
                        <td>${Math.round(p.budget_remaining).toLocaleString("es-CL")}</td>
                        <td>${Math.round(p.cost_per_enrollment).toLocaleString("es-CL")}</td>
                        <td>${Math.round(p.cost_per_refill).toLocaleString("es-CL")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}

        {activeTab === "charges" && (
          <section>
            <h2>Historial de Cargos</h2>
            {charges.length === 0 ? (
              <p className="empty-state">No hay cargos registrados.</p>
            ) : (
              <div className="data-table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Fecha</th>
                      <th>Tipo</th>
                      <th>Monto</th>
                      <th>Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {charges.map((c) => (
                      <tr key={c.id}>
                        <td>{new Date(c.created_at).toLocaleDateString("es-CL")}</td>
                        <td>{c.charge_type}</td>
                        <td>${Math.round(c.amount).toLocaleString("es-CL")}</td>
                        <td><span className={`status-badge status-${c.status}`}>{c.status}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}
      </div>
    </div>
  );
}
