import React from "react";

export default function WinRateChart({ data }) {
  if (!data || data.length === 0) return null;

  const maxRate = Math.max(...data.map((d) => d.win_rate_pct), 1);

  return (
    <div className="win-rate-chart">
      {data.slice(0, 15).map((item) => (
        <div key={item.supplier} className="win-rate-chart__row">
          <div className="win-rate-chart__label">
            <span className="win-rate-chart__supplier">{item.supplier}</span>
            <span className="win-rate-chart__stats">{item.wins}/{item.total_bids} bids</span>
          </div>
          <div className="win-rate-chart__bar-container">
            <div
              className="win-rate-chart__bar"
              style={{ width: `${(item.win_rate_pct / maxRate) * 100}%` }}
            />
            <span className="win-rate-chart__value">{item.win_rate_pct}%</span>
          </div>
        </div>
      ))}
    </div>
  );
}
