import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import useGpo from "../hooks/useGpo";
import GpoSidebar from "../components/GpoSidebar";
import DemandAggregationCard from "../components/DemandAggregationCard";

export default function GpoPurchaseIntentPage() {
  const { slug } = useParams();
  const { group, intents, demand, loading, loadIntents, loadDemand, submitIntent, cancelIntent } = useGpo(slug);
  const [productName, setProductName] = useState("");
  const [quantity, setQuantity] = useState("");
  const [targetMonth, setTargetMonth] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
  });
  const [submitMsg, setSubmitMsg] = useState("");

  useEffect(() => {
    loadIntents(targetMonth);
    loadDemand(targetMonth);
  }, [loadIntents, loadDemand, targetMonth]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!productName || !quantity) return;
    try {
      await submitIntent({
        product_name: productName,
        quantity_units: parseInt(quantity),
        target_month: targetMonth,
      });
      setSubmitMsg("Intención registrada");
      setProductName("");
      setQuantity("");
      loadDemand(targetMonth);
    } catch (err) {
      setSubmitMsg(err.response?.data?.detail || "Error al registrar");
    }
  };

  if (loading) {
    return <div className="loading-state"><div className="spinner"></div></div>;
  }

  return (
    <div className="org-layout container">
      <GpoSidebar slug={slug} />
      <div className="org-main">
        <h1>Intenciones de Compra</h1>

        <form className="intent-form" onSubmit={handleSubmit}>
          <div className="intent-form__fields">
            <input className="input" placeholder="Nombre del producto" value={productName} onChange={(e) => setProductName(e.target.value)} required />
            <input className="input" type="number" placeholder="Cantidad (unidades)" value={quantity} onChange={(e) => setQuantity(e.target.value)} min={1} required />
            <input className="input" type="month" value={targetMonth} onChange={(e) => setTargetMonth(e.target.value)} />
            <button className="btn btn--primary" type="submit">Registrar</button>
          </div>
          {submitMsg && <p className="alert-msg">{submitMsg}</p>}
        </form>

        {demand.length > 0 && (
          <section className="gpo-section">
            <h2>Demanda Agregada — {targetMonth}</h2>
            <div className="demand-grid">
              {demand.map((item, i) => (
                <DemandAggregationCard key={i} item={item} />
              ))}
            </div>
          </section>
        )}

        <section className="gpo-section">
          <h2>Mis Intenciones</h2>
          {intents.length === 0 ? (
            <p className="empty-state">No has registrado intenciones para este mes.</p>
          ) : (
            <div className="data-table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Producto</th>
                    <th>Cantidad</th>
                    <th>Mes</th>
                    <th>Estado</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {intents.map((intent) => (
                    <tr key={intent.id}>
                      <td>{intent.product_name}</td>
                      <td>{intent.quantity_units?.toLocaleString("es-CL")}</td>
                      <td>{intent.target_month}</td>
                      <td><span className={`status-badge status-${intent.status}`}>{intent.status}</span></td>
                      <td>
                        {intent.status === "submitted" && (
                          <button className="btn btn--danger btn--sm" onClick={() => cancelIntent(intent.id)}>Cancelar</button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
