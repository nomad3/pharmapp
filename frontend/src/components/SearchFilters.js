import { useState } from 'react';

const DRUG_FORMS = ['Comprimido', 'Capsula', 'Liquido', 'Crema', 'Inyectable', 'Jarabe', 'Gotas'];
const CHAINS = [
  { value: 'cruz_verde', label: 'Cruz Verde' },
  { value: 'salcobrand', label: 'Salcobrand' },
  { value: 'ahumada', label: 'Ahumada' },
  { value: 'dr_simi', label: 'Dr. Simi' },
];

export default function SearchFilters({ filters, onFilterChange }) {
  const [expanded, setExpanded] = useState(false);

  const handleChange = (key, value) => {
    onFilterChange({ ...filters, [key]: value });
  };

  const clearFilters = () => {
    onFilterChange({ form: '', requires_prescription: '', chain: '', price_min: '', price_max: '' });
  };

  const hasFilters = Object.values(filters).some(v => v !== '' && v !== undefined);

  return (
    <div className="search-filters">
      <button className="filters-toggle" onClick={() => setExpanded(!expanded)}>
        Filtros {hasFilters && `(${Object.values(filters).filter(v => v !== '' && v !== undefined).length})`}
        <span>{expanded ? '\u25B2' : '\u25BC'}</span>
      </button>

      {expanded && (
        <div className="filters-panel">
          <div className="filter-group">
            <label>Forma farmaceutica</label>
            <select value={filters.form || ''} onChange={e => handleChange('form', e.target.value)}>
              <option value="">Todas</option>
              {DRUG_FORMS.map(f => <option key={f} value={f}>{f}</option>)}
            </select>
          </div>

          <div className="filter-group">
            <label>Receta medica</label>
            <select value={filters.requires_prescription ?? ''} onChange={e => handleChange('requires_prescription', e.target.value)}>
              <option value="">Todos</option>
              <option value="true">Con receta</option>
              <option value="false">Sin receta</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Cadena farmaceutica</label>
            <select value={filters.chain || ''} onChange={e => handleChange('chain', e.target.value)}>
              <option value="">Todas</option>
              {CHAINS.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
            </select>
          </div>

          <div className="filter-group">
            <label>Rango de precio (CLP)</label>
            <div className="price-range">
              <input type="number" placeholder="Min" value={filters.price_min || ''} onChange={e => handleChange('price_min', e.target.value)} />
              <span>&mdash;</span>
              <input type="number" placeholder="Max" value={filters.price_max || ''} onChange={e => handleChange('price_max', e.target.value)} />
            </div>
          </div>

          {hasFilters && (
            <button className="clear-filters" onClick={clearFilters}>Limpiar filtros</button>
          )}
        </div>
      )}
    </div>
  );
}
