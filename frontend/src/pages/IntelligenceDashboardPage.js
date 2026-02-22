import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import client from "../api/client";
import OrgSidebar from "../components/OrgSidebar";
import ForecastTable from "../components/charts/ForecastTable";
import WinRateChart from "../components/charts/WinRateChart";
import MarketShareTrendChart from "../components/charts/MarketShareTrendChart";
import RegionalHeatmap from "../components/charts/RegionalHeatmap";
import ReportBuilder from "../components/ReportBuilder";

export default function IntelligenceDashboardPage() {
  const { slug } = useParams();
  const [activeTab, setActiveTab] = useState("forecasting");
  const [forecasts, setForecasts] = useState([]);
  const [marketTrends, setMarketTrends] = useState([]);
  const [winRates, setWinRates] = useState([]);
  const [newEntrants, setNewEntrants] = useState([]);
  const [heatmap, setHeatmap] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [fc, mt, wr, ne, hm] = await Promise.all([
          client.get("/data/forecasts?days_ahead=90").catch(() => ({ data: [] })),
          client.get("/data/competitive/market-share-trends").catch(() => ({ data: [] })),
          client.get("/data/competitive/supplier-win-rates").catch(() => ({ data: [] })),
          client.get("/data/competitive/new-entrants").catch(() => ({ data: [] })),
          client.get("/data/regional-heatmap").catch(() => ({ data: [] })),
        ]);
        setForecasts(fc.data);
        setMarketTrends(mt.data);
        setWinRates(wr.data);
        setNewEntrants(ne.data);
        setHeatmap(hm.data);
      } catch (err) {
        console.error("Error loading intelligence data:", err);
      }
      setLoading(false);
    };
    fetchData();
  }, []);

  const tabs = [
    { id: "forecasting", label: "Forecasting" },
    { id: "competitive", label: "Competencia" },
    { id: "regional", label: "Regional" },
    { id: "reports", label: "Reportes" },
  ];

  return (
    <div className="org-layout container">
      {slug && <OrgSidebar slug={slug} />}
      <div className="org-main">
        <h1>Intelligence Dashboard</h1>

        <div className="tab-nav">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`tab-btn ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Cargando datos...</p>
          </div>
        ) : (
          <div className="tab-content">
            {activeTab === "forecasting" && (
              <section className="intel-section">
                <h2>Oportunidades de Licitación ({forecasts.length})</h2>
                <ForecastTable data={forecasts} />
              </section>
            )}

            {activeTab === "competitive" && (
              <>
                <section className="intel-section">
                  <h2>Market Share Trends</h2>
                  <MarketShareTrendChart data={marketTrends} />
                </section>
                <section className="intel-section">
                  <h2>Tasa de Adjudicación por Proveedor</h2>
                  <WinRateChart data={winRates} />
                </section>
                <section className="intel-section">
                  <h2>Nuevos Participantes</h2>
                  {newEntrants.length > 0 ? (
                    <div className="data-table-wrapper">
                      <table className="data-table">
                        <thead>
                          <tr>
                            <th>Proveedor</th>
                            <th>Primera Aparición</th>
                            <th>Unidades</th>
                            <th>Revenue</th>
                          </tr>
                        </thead>
                        <tbody>
                          {newEntrants.map((e, i) => (
                            <tr key={i}>
                              <td>{e.supplier}</td>
                              <td>{e.first_seen}</td>
                              <td>{e.total_units?.toLocaleString("es-CL")}</td>
                              <td>${Math.round(e.total_revenue).toLocaleString("es-CL")}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="empty-state">No se detectaron nuevos participantes.</p>
                  )}
                </section>
              </>
            )}

            {activeTab === "regional" && (
              <section className="intel-section">
                <h2>Demanda Regional</h2>
                <RegionalHeatmap data={heatmap} />
              </section>
            )}

            {activeTab === "reports" && (
              <section className="intel-section">
                <h2>Constructor de Reportes</h2>
                <ReportBuilder />
              </section>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
