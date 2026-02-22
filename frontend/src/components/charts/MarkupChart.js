import React from "react";

export default function MarkupChart({ data }) {
  if (!data || data.length === 0) return null;

  const maxMarkup = Math.max(...data.map((d) => d.avg_markup_pct));

  return (
    <div className="markup-chart">
      {data.map((item) => {
        const widthPct = maxMarkup > 0 ? (item.avg_markup_pct / maxMarkup) * 100 : 0;
        const barColor =
          item.transparency_score >= 70
            ? "var(--primary)"
            : item.transparency_score >= 40
            ? "#f59e0b"
            : "#ef4444";

        return (
          <div key={item.chain} className="markup-chart__row">
            <div className="markup-chart__label">
              <span className="markup-chart__chain">{item.chain}</span>
              <span className="markup-chart__score">Score: {item.transparency_score}</span>
            </div>
            <div className="markup-chart__bar-container">
              <div
                className="markup-chart__bar"
                style={{ width: `${widthPct}%`, backgroundColor: barColor }}
              />
              <span className="markup-chart__value">+{Math.round(item.avg_markup_pct)}%</span>
            </div>
            <div className="markup-chart__count">{item.medication_count} meds</div>
          </div>
        );
      })}
    </div>
  );
}
