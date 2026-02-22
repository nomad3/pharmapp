import React from "react";

const DEFAULT_TIERS = [
  { label: "Base", refills: 0, discount: "0%" },
  { label: "Bronce", refills: 3, discount: "5%" },
  { label: "Plata", refills: 6, discount: "10%" },
  { label: "Oro", refills: 12, discount: "15%" },
];

export default function DiscountTierProgress({ currentRefills = 0, tiers, currentDiscount = 0 }) {
  const displayTiers = tiers && tiers.length > 0
    ? tiers.map((t) => ({
        label: `${Math.round(t.discount_pct * 100)}%`,
        refills: t.min_consecutive_refills,
        discount: `${Math.round(t.discount_pct * 100)}%`,
      }))
    : DEFAULT_TIERS;

  return (
    <div className="tier-progress">
      <div className="tier-progress__track">
        {displayTiers.map((tier, i) => {
          const isActive = currentRefills >= tier.refills;
          const isCurrent = i < displayTiers.length - 1
            ? currentRefills >= tier.refills && currentRefills < displayTiers[i + 1].refills
            : currentRefills >= tier.refills;

          return (
            <div key={i} className={`tier-progress__step ${isActive ? "tier-progress__step--active" : ""} ${isCurrent ? "tier-progress__step--current" : ""}`}>
              <div className="tier-progress__dot" />
              <div className="tier-progress__info">
                <span className="tier-progress__discount">{tier.discount}</span>
                <span className="tier-progress__refills">{tier.refills}+ refills</span>
              </div>
              {i < displayTiers.length - 1 && <div className={`tier-progress__connector ${isActive ? "tier-progress__connector--active" : ""}`} />}
            </div>
          );
        })}
      </div>
    </div>
  );
}
