import React from "react";
import { Link, useLocation } from "react-router-dom";

export default function GpoSidebar({ slug }) {
  const location = useLocation();
  const base = `/gpo/${slug}`;

  const links = [
    { to: base, label: "Dashboard", icon: "M18 20V10M12 20V4M6 20v-6" },
    { to: `${base}/intents`, label: "Intenciones", icon: "M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2M9 5a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2" },
    { to: `${base}/savings`, label: "Ahorros", icon: "M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" },
  ];

  return (
    <aside className="org-sidebar">
      <nav className="org-sidebar__nav">
        {links.map((link) => (
          <Link
            key={link.to}
            to={link.to}
            className={`org-sidebar__link ${location.pathname === link.to ? "active" : ""}`}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d={link.icon} />
            </svg>
            <span>{link.label}</span>
          </Link>
        ))}
      </nav>
    </aside>
  );
}
