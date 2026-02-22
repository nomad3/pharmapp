import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client from "../api/client";
import SummaryCards from "../components/charts/SummaryCards";
import MarketShareChart from "../components/charts/MarketShareChart";
import SalesTrendChart from "../components/charts/SalesTrendChart";
import TopInstitutionsTable from "../components/charts/TopInstitutionsTable";
import RegionChart from "../components/charts/RegionChart";
import DrugPriceChart from "../components/charts/DrugPriceChart";

export default function AnalyticsDashboardPage() {
  const [tab, setTab] = useState("cenabast");
  const [loading, setLoading] = useState(true);
  const [drugFilter, setDrugFilter] = useState("");
  const [regionFilter, setRegionFilter] = useState("");

  // BMS state
  const [summary, setSummary] = useState(null);
  const [marketShare, setMarketShare] = useState([]);
  const [bmsTrends, setBmsTrends] = useState([]);
  const [topInstitutions, setTopInstitutions] = useState([]);
  const [bmsRegions, setBmsRegions] = useState([]);
  const [drugPrices, setDrugPrices] = useState([]);

  // Cenabast state
  const [cenabastTrends, setCenabastTrends] = useState([]);
  const [cenabastPharmacies, setCenabastPharmacies] = useState([]);
  const [cenabastProducts, setCenabastProducts] = useState([]);
  const [cenabastRegions, setCenabastRegions] = useState([]);

  // Drug options for filter
  const [drugOptions, setDrugOptions] = useState([]);
  const [regionOptions, setRegionOptions] = useState([]);

  useEffect(() => {
    loadSummary();
  }, []);

  useEffect(() => {
    if (tab === "bms") loadBmsData();
    else loadCenabastData();
  }, [tab, drugFilter, regionFilter]); // eslint-disable-line react-hooks/exhaustive-deps

  async function loadSummary() {
    try {
      const res = await client.get("/analytics/summary");
      setSummary(res.data);
    } catch (e) {
      console.error("Failed to load summary", e);
    }
  }

  async function loadBmsData() {
    setLoading(true);
    try {
      const params = {};
      if (drugFilter) params.drug = drugFilter;
      if (regionFilter) params.region = regionFilter;

      const [ms, tr, ti, rg, dp] = await Promise.all([
        client.get("/analytics/market-share", { params: { market: params.drug } }),
        client.get("/analytics/trends", { params }),
        client.get("/analytics/top-institutions", { params: { limit: 20, region: regionFilter || undefined } }),
        client.get("/analytics/regions"),
        client.get("/analytics/drug-prices", { params }),
      ]);

      setMarketShare(ms.data);
      setBmsTrends(tr.data);
      setTopInstitutions(ti.data);
      setBmsRegions(rg.data);
      setDrugPrices(dp.data);

      // Build filter options from data
      if (ms.data.length > 0 && drugOptions.length === 0) {
        const drugs = [...new Set(ms.data.map((d) => d.drug).filter(Boolean))].sort();
        setDrugOptions(drugs);
      }
      if (rg.data.length > 0 && regionOptions.length === 0) {
        const regions = rg.data.map((d) => d.region).filter(Boolean).sort();
        setRegionOptions(regions);
      }
    } catch (e) {
      console.error("Failed to load BMS data", e);
    }
    setLoading(false);
  }

  async function loadCenabastData() {
    setLoading(true);
    try {
      const [tr, ph, pr, rg] = await Promise.all([
        client.get("/analytics/cenabast/trends", { params: drugFilter ? { product: drugFilter } : {} }),
        client.get("/analytics/cenabast/top-pharmacies", { params: { limit: 20, region: regionFilter || undefined } }),
        client.get("/analytics/cenabast/top-products", { params: { limit: 20 } }),
        client.get("/analytics/cenabast/regions"),
      ]);

      setCenabastTrends(tr.data);
      setCenabastPharmacies(ph.data);
      setCenabastProducts(pr.data);
      setCenabastRegions(rg.data);

      if (rg.data.length > 0 && regionOptions.length === 0) {
        const regions = rg.data.map((d) => d.region).filter(Boolean).sort();
        setRegionOptions(regions);
      }
    } catch (e) {
      console.error("Failed to load Cenabast data", e);
    }
    setLoading(false);
  }

  const pharmacyCols = [
    { key: "nombre", label: "Farmacia", fmt: (v) => v || "—" },
    { key: "comuna", label: "Comuna", fmt: (v) => v || "—" },
    { key: "region", label: "Región", fmt: (v) => v || "—" },
    { key: "total_units", label: "Unidades", fmt: (v) => (v || 0).toLocaleString("es-CL") },
    { key: "total_revenue", label: "Revenue", fmt: (v) => `$${Math.round(v || 0).toLocaleString("es-CL")}` },
  ];

  const productCols = [
    { key: "nombre", label: "Producto", fmt: (v) => v && v.length > 40 ? v.slice(0, 40) + "..." : (v || "—") },
    { key: "total_units", label: "Unidades", fmt: (v) => (v || 0).toLocaleString("es-CL") },
    { key: "total_revenue", label: "Revenue", fmt: (v) => `$${Math.round(v || 0).toLocaleString("es-CL")}` },
    { key: "precio_maximo", label: "PMVP", fmt: (v) => v ? `$${Math.round(v).toLocaleString("es-CL")}` : "—" },
  ];

  return (
    <div className="analytics-page">
      <div className="container">
        <div className="analytics-header">
          <h1 className="page-title">Market Intelligence</h1>
          <div className="analytics-header-actions">
            <div className="analytics-tabs">
              <button className={`tab-btn ${tab === "cenabast" ? "active" : ""}`} onClick={() => { setTab("cenabast"); setDrugFilter(""); setRegionFilter(""); }}>
                Cenabast Farmacias
              </button>
              <button className={`tab-btn ${tab === "bms" ? "active" : ""}`} onClick={() => { setTab("bms"); setDrugFilter(""); setRegionFilter(""); }}>
                BMS Oncología
              </button>
            </div>
            <div className="analytics-upgrade-cta">
              <Link to="/pricing" className="btn btn--sm btn--primary">
                Acceso API programático
              </Link>
            </div>
          </div>
        </div>

        <SummaryCards data={summary} />

        <div className="analytics-filters">
          {tab === "bms" && drugOptions.length > 0 && (
            <select value={drugFilter} onChange={(e) => setDrugFilter(e.target.value)}>
              <option value="">Todas las drogas</option>
              {drugOptions.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
          )}
          {tab === "cenabast" && (
            <input
              type="text"
              placeholder="Buscar producto..."
              value={drugFilter}
              onChange={(e) => setDrugFilter(e.target.value)}
              className="filter-input"
            />
          )}
          {regionOptions.length > 0 && (
            <select value={regionFilter} onChange={(e) => setRegionFilter(e.target.value)}>
              <option value="">Todas las regiones</option>
              {regionOptions.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          )}
        </div>

        {loading ? (
          <div className="loading-state">
            <div className="spinner" />
            <p>Cargando datos...</p>
          </div>
        ) : tab === "bms" ? (
          <>
            <div className="chart-grid-2">
              <MarketShareChart data={marketShare} />
              <SalesTrendChart data={bmsTrends} title="Tendencia BMS vs Competencia" />
            </div>
            <TopInstitutionsTable data={topInstitutions} title="Top 20 Instituciones (BMS)" />
            <div className="chart-grid-2">
              <RegionChart data={bmsRegions} title="Distribución Regional BMS" color="#00695C" />
              <DrugPriceChart data={drugPrices} />
            </div>
          </>
        ) : (
          <>
            <div className="chart-grid-2">
              <SalesTrendChart data={cenabastTrends} title="Tendencia Cenabast Farmacias Privadas" isCenabast />
              <RegionChart data={cenabastRegions} title="Revenue por Región" color="#1565C0" />
            </div>
            <TopInstitutionsTable data={cenabastPharmacies} title="Top 20 Farmacias Privadas (Cenabast)" columns={pharmacyCols} />
            <TopInstitutionsTable data={cenabastProducts} title="Top 20 Productos (Cenabast)" columns={productCols} />
          </>
        )}
      </div>
    </div>
  );
}
