import React from "react";

export default function MarketShareTrendChart({ data }) {
  if (!data || data.length === 0) return null;

  // Group by period
  const periods = {};
  data.forEach((item) => {
    if (!periods[item.period]) {
      periods[item.period] = {};
    }
    periods[item.period][item.provider] = {
      units: item.units,
      revenue: item.revenue,
    };
  });

  const providers = [...new Set(data.map((d) => d.provider))].slice(0, 5);
  const sortedPeriods = Object.keys(periods).sort();
  const maxRevenue = Math.max(
    ...data.map((d) => d.revenue),
    1
  );

  return (
    <div className="market-trend-chart">
      <div className="market-trend-chart__legend">
        {providers.map((p, i) => (
          <span key={p} className="market-trend-chart__legend-item">
            <span className={`legend-dot legend-dot--${i}`} />
            {p}
          </span>
        ))}
      </div>
      <div className="market-trend-chart__grid">
        {sortedPeriods.slice(-12).map((period) => (
          <div key={period} className="market-trend-chart__column">
            <div className="market-trend-chart__bars">
              {providers.map((p, i) => {
                const val = periods[period]?.[p]?.revenue || 0;
                const heightPct = (val / maxRevenue) * 100;
                return (
                  <div
                    key={p}
                    className={`market-trend-chart__bar bar-color--${i}`}
                    style={{ height: `${heightPct}%` }}
                    title={`${p}: $${Math.round(val).toLocaleString("es-CL")}`}
                  />
                );
              })}
            </div>
            <div className="market-trend-chart__label">{period.slice(5)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
