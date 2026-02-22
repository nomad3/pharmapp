import React from "react";
import { Link } from "react-router-dom";

export default function PremiumGate({ children, isPremium, featureName }) {
  if (isPremium) {
    return <>{children}</>;
  }

  return (
    <div className="premium-gate">
      <div className="premium-gate__overlay">
        <div className="premium-gate__cta">
          <span className="premium-gate__icon">🔒</span>
          <p>{featureName || "Esta función"} es exclusiva para usuarios Premium</p>
          <Link to="/premium" className="btn btn--primary btn--sm">
            Activar Premium
          </Link>
        </div>
      </div>
      <div className="premium-gate__preview">
        {children}
      </div>
    </div>
  );
}
