import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import client from '../api/client';

export default function Autocomplete() {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const navigate = useNavigate();
  const timerRef = useRef(null);
  const wrapperRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleChange = (e) => {
    const val = e.target.value;
    setQuery(val);
    setSelectedIndex(-1);

    if (timerRef.current) clearTimeout(timerRef.current);

    if (val.length < 2) {
      setSuggestions([]);
      setShowDropdown(false);
      return;
    }

    timerRef.current = setTimeout(async () => {
      try {
        const { data } = await client.get(`/medications/autocomplete?q=${encodeURIComponent(val)}`);
        setSuggestions(data);
        setShowDropdown(data.length > 0);
      } catch {
        setSuggestions([]);
      }
    }, 300);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (selectedIndex >= 0 && suggestions[selectedIndex]) {
        const s = suggestions[selectedIndex];
        navigate(`/medicamento/${s.slug || s.id}`);
      } else if (query.trim()) {
        navigate(`/search?q=${encodeURIComponent(query.trim())}`);
      }
      setShowDropdown(false);
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => Math.min(prev + 1, suggestions.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => Math.max(prev - 1, -1));
    } else if (e.key === 'Escape') {
      setShowDropdown(false);
    }
  };

  const handleSelect = (suggestion) => {
    navigate(`/medicamento/${suggestion.slug || suggestion.id}`);
    setShowDropdown(false);
    setQuery('');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
      setShowDropdown(false);
    }
  };

  return (
    <div className="autocomplete-wrapper" ref={wrapperRef}>
      <form onSubmit={handleSubmit} className="autocomplete-form">
        <input
          type="text"
          value={query}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onFocus={() => suggestions.length > 0 && setShowDropdown(true)}
          placeholder="Buscar medicamento..."
          className="autocomplete-input"
        />
        <button type="submit" className="autocomplete-btn">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        </button>
      </form>
      {showDropdown && (
        <ul className="autocomplete-dropdown">
          {suggestions.map((s, i) => (
            <li
              key={s.id}
              className={`autocomplete-item ${i === selectedIndex ? 'selected' : ''}`}
              onMouseDown={() => handleSelect(s)}
              onMouseEnter={() => setSelectedIndex(i)}
            >
              {s.name}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
