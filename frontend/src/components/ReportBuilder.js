import React, { useState } from "react";
import client from "../api/client";

const DATASETS = [
  { value: "market-share", label: "Market Share" },
  { value: "sales-trends", label: "Sales Trends" },
  { value: "top-institutions", label: "Top Institutions" },
  { value: "regional", label: "Regional Distribution" },
  { value: "cenabast-trends", label: "Cenabast Trends" },
  { value: "cenabast-top-products", label: "Cenabast Top Products" },
  { value: "forecasts", label: "Tender Forecasts" },
  { value: "market-share-trends", label: "Market Share Trends" },
  { value: "supplier-win-rates", label: "Supplier Win Rates" },
  { value: "new-entrants", label: "New Entrants" },
  { value: "price-positioning", label: "Price Positioning" },
  { value: "regional-heatmap", label: "Regional Heatmap" },
];

export default function ReportBuilder() {
  const [dataset, setDataset] = useState("market-share");
  const [filterProduct, setFilterProduct] = useState("");
  const [filterRegion, setFilterRegion] = useState("");
  const [filterSupplier, setFilterSupplier] = useState("");
  const [limit, setLimit] = useState(100);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleExecute = async () => {
    setLoading(true);
    setError("");
    try {
      const filters = {};
      if (filterProduct) filters.product = filterProduct;
      if (filterRegion) filters.region = filterRegion;
      if (filterSupplier) filters.supplier = filterSupplier;

      const { data } = await client.post("/reports/execute", {
        dataset,
        filters,
        limit,
      });
      setResults(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Error ejecutando reporte");
    }
    setLoading(false);
  };

  const handleExportCsv = async () => {
    try {
      const filters = {};
      if (filterProduct) filters.product = filterProduct;
      if (filterRegion) filters.region = filterRegion;
      if (filterSupplier) filters.supplier = filterSupplier;

      const response = await client.post(
        "/reports/execute/csv",
        { dataset, filters, limit },
        { responseType: "blob" }
      );
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `${dataset}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError("Error exportando CSV");
    }
  };

  return (
    <div className="report-builder">
      <div className="report-builder__controls">
        <div className="report-builder__field">
          <label>Dataset</label>
          <select className="input" value={dataset} onChange={(e) => setDataset(e.target.value)}>
            {DATASETS.map((d) => (
              <option key={d.value} value={d.value}>{d.label}</option>
            ))}
          </select>
        </div>
        <div className="report-builder__field">
          <label>Producto</label>
          <input className="input" value={filterProduct} onChange={(e) => setFilterProduct(e.target.value)} placeholder="Filtrar por producto" />
        </div>
        <div className="report-builder__field">
          <label>Región</label>
          <input className="input" value={filterRegion} onChange={(e) => setFilterRegion(e.target.value)} placeholder="Filtrar por región" />
        </div>
        <div className="report-builder__field">
          <label>Proveedor</label>
          <input className="input" value={filterSupplier} onChange={(e) => setFilterSupplier(e.target.value)} placeholder="Filtrar por proveedor" />
        </div>
        <div className="report-builder__field">
          <label>Límite</label>
          <input className="input" type="number" value={limit} onChange={(e) => setLimit(parseInt(e.target.value) || 100)} min={1} max={1000} />
        </div>
        <div className="report-builder__actions">
          <button className="btn btn--primary" onClick={handleExecute} disabled={loading}>
            {loading ? "Ejecutando..." : "Ejecutar"}
          </button>
          <button className="btn btn--secondary" onClick={handleExportCsv} disabled={!results}>
            Exportar CSV
          </button>
        </div>
      </div>

      {error && <p className="error-msg">{error}</p>}

      {results && Array.isArray(results) && results.length > 0 && (
        <div className="data-table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                {Object.keys(results[0]).map((key) => (
                  <th key={key}>{key}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {results.map((row, i) => (
                <tr key={i}>
                  {Object.values(row).map((val, j) => (
                    <td key={j}>
                      {typeof val === "number"
                        ? val % 1 === 0
                          ? val.toLocaleString("es-CL")
                          : val.toLocaleString("es-CL", { maximumFractionDigits: 1 })
                        : String(val ?? "")}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
