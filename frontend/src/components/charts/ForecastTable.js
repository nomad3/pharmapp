import React from "react";

export default function ForecastTable({ data }) {
  if (!data || data.length === 0) {
    return <p className="empty-state">No hay oportunidades de licitación próximas.</p>;
  }

  const confidenceColor = (level) => {
    switch (level) {
      case "high": return "confidence-high";
      case "medium": return "confidence-medium";
      default: return "confidence-low";
    }
  };

  return (
    <div className="data-table-wrapper">
      <table className="data-table">
        <thead>
          <tr>
            <th>Producto</th>
            <th>Institución</th>
            <th>Fecha Estimada</th>
            <th>Días</th>
            <th>Valor Estimado</th>
            <th>Cant. Promedio</th>
            <th>Confianza</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item, i) => (
            <tr key={i}>
              <td className="med-name-cell">{item.product}</td>
              <td>{item.institution_name || item.institution_rut}</td>
              <td>{item.predicted_date}</td>
              <td>
                <span className={item.days_until <= 30 ? "days-urgent" : ""}>
                  {item.days_until}d
                </span>
              </td>
              <td>${Math.round(item.estimated_value).toLocaleString("es-CL")}</td>
              <td>{item.avg_quantity?.toLocaleString("es-CL")}</td>
              <td>
                <span className={`confidence-badge ${confidenceColor(item.confidence_level)}`}>
                  {item.confidence_level}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
