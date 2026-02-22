import React, { useState } from "react";
import { useParams } from "react-router-dom";
import client from "../api/client";
import OrgSidebar from "../components/OrgSidebar";
import useOrg from "../hooks/useOrg";

export default function BillingPage() {
  const { slug } = useParams();
  const { org, loading } = useOrg(slug);
  const [redirecting, setRedirecting] = useState(false);

  const handleManageBilling = async () => {
    setRedirecting(true);
    try {
      const { data } = await client.post("/billing/portal", { org_slug: slug });
      window.location.href = data.portal_url;
    } catch (err) {
      alert(err.response?.data?.detail || "Error al abrir portal de facturación");
      setRedirecting(false);
    }
  };

  const handleUpgrade = async (tier) => {
    setRedirecting(true);
    try {
      const { data } = await client.post("/billing/checkout", { tier, org_slug: slug });
      window.location.href = data.checkout_url;
    } catch (err) {
      alert(err.response?.data?.detail || "Error al iniciar checkout");
      setRedirecting(false);
    }
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
          <h1 className="page-title">Facturación — {org?.name}</h1>

          <div className="billing-actions">
            <div className="billing-card">
              <h2>Plan actual</h2>
              <p className="billing-tier">Free</p>
              <p>100 requests/día, 10 requests/min</p>
            </div>

            <div className="billing-card">
              <h2>Upgrade a Pro</h2>
              <p className="billing-price">$500 USD/mes</p>
              <p>10,000 requests/día, 100 requests/min, CSV export</p>
              <button className="btn btn--primary" onClick={() => handleUpgrade("pro")} disabled={redirecting}>
                {redirecting ? "Redirigiendo..." : "Upgrade a Pro"}
              </button>
            </div>

            <div className="billing-card">
              <h2>Enterprise</h2>
              <p className="billing-price">$5,000 USD/mes</p>
              <p>Requests ilimitados, 1000 req/min, SLA 99.9%</p>
              <button className="btn btn--secondary" onClick={() => handleUpgrade("enterprise")} disabled={redirecting}>
                {redirecting ? "Redirigiendo..." : "Upgrade a Enterprise"}
              </button>
            </div>
          </div>

          <div className="billing-portal">
            <button className="btn btn--secondary" onClick={handleManageBilling} disabled={redirecting}>
              {redirecting ? "Redirigiendo..." : "Administrar facturación en Stripe"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
