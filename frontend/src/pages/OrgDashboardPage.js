import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import client from "../api/client";
import OrgSidebar from "../components/OrgSidebar";
import SummaryCards from "../components/charts/SummaryCards";
import MarketShareChart from "../components/charts/MarketShareChart";
import SalesTrendChart from "../components/charts/SalesTrendChart";
import RegionChart from "../components/charts/RegionChart";
import UsageChart from "../components/UsageChart";
import useOrg from "../hooks/useOrg";

export default function OrgDashboardPage() {
  const { slug } = useParams();
  const { org, loading: orgLoading } = useOrg(slug);
  const [summary, setSummary] = useState(null);
  const [marketShare, setMarketShare] = useState([]);
  const [trends, setTrends] = useState([]);
  const [regions, setRegions] = useState([]);
  const [usage, setUsage] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!org) return;
    loadData();
  }, [org]); // eslint-disable-line react-hooks/exhaustive-deps

  async function loadData() {
    setLoading(true);
    try {
      const [s, ms, tr, rg] = await Promise.all([
        client.get("/analytics/summary"),
        client.get("/analytics/market-share"),
        client.get("/analytics/trends"),
        client.get("/analytics/regions"),
      ]);
      setSummary(s.data);
      setMarketShare(ms.data);
      setTrends(tr.data);
      setRegions(rg.data);

      // Load API usage for first key
      try {
        const keys = await client.get(`/api-keys/?org_slug=${slug}`);
        if (keys.data.length > 0) {
          const usageRes = await client.get(`/api-keys/${keys.data[0].id}/usage`);
          setUsage(usageRes.data.top_endpoints || []);
        }
      } catch (e) { /* no keys yet */ }
    } catch (e) {
      console.error("Failed to load dashboard data", e);
    }
    setLoading(false);
  }

  const handleExport = async (dataset) => {
    try {
      const orgSlug = localStorage.getItem("org_slug");
      const keys = await client.get(`/api-keys/?org_slug=${orgSlug}`);
      if (keys.data.length === 0) {
        alert("Crea una API key primero para exportar datos");
        return;
      }
      window.open(`/api/v1/data/export?dataset=${dataset}`, "_blank");
    } catch (e) {
      console.error("Export failed", e);
    }
  };

  if (orgLoading || loading) {
    return (
      <div className="loading-state">
        <div className="spinner"></div>
        <p>Cargando dashboard...</p>
      </div>
    );
  }

  return (
    <div className="org-page">
      <OrgSidebar slug={slug} />
      <div className="org-content">
        <div className="container">
          <div className="org-dashboard-header">
            <h1 className="page-title">{org?.name || "Dashboard"}</h1>
            <div className="export-buttons">
              <button className="btn btn--sm btn--secondary" onClick={() => handleExport("market-share")}>
                Exportar Market Share
              </button>
              <button className="btn btn--sm btn--secondary" onClick={() => handleExport("trends")}>
                Exportar Tendencias
              </button>
              <button className="btn btn--sm btn--secondary" onClick={() => handleExport("regions")}>
                Exportar Regiones
              </button>
            </div>
          </div>

          <SummaryCards data={summary} />

          <div className="chart-grid-2">
            <MarketShareChart data={marketShare} />
            <SalesTrendChart data={trends} title="Tendencias de mercado" />
          </div>

          <div className="chart-grid-2">
            <RegionChart data={regions} title="Distribución regional" color="#00695C" />
            <UsageChart data={usage} title="Uso de API (top endpoints)" />
          </div>
        </div>
      </div>
    </div>
  );
}
