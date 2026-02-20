import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function SearchBar({ compact }) {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  const handleSearch = (e) => {
    e.preventDefault();
    if (query.trim()) navigate(`/search?q=${encodeURIComponent(query.trim())}`);
  };

  return (
    <form onSubmit={handleSearch} className="search-bar">
      <input
        type="text"
        placeholder={compact ? "Buscar medicamento..." : "Buscar por nombre, principio activo o laboratorio..."}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <button type="submit">
        <span className="search-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        </span>
        {!compact && <span>Buscar</span>}
      </button>
    </form>
  );
}
