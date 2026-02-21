import { Search } from "lucide-react";

const CATEGORIES = ["", "billing", "technical", "account", "general"];
const PRIORITIES = ["", "low", "medium", "high", "critical"];
const STATUSES = ["", "open", "in_progress", "resolved", "closed"];

export default function FilterBar({ filters, onChange }) {
  const handle = (key) => (e) => onChange({ ...filters, [key]: e.target.value });

  return (
    <div className="filter-bar">
      <div style={{ position: "relative", flex: 2, minWidth: 200 }}>
        <Search size={14} style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
        <input
          className="form-input"
          style={{ paddingLeft: 32 }}
          placeholder="Search tickets…"
          value={filters.search}
          onChange={handle("search")}
        />
      </div>

      <select className="form-select" value={filters.category} onChange={handle("category")}>
        <option value="">All Categories</option>
        {CATEGORIES.filter(Boolean).map((c) => (
          <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
        ))}
      </select>

      <select className="form-select" value={filters.priority} onChange={handle("priority")}>
        <option value="">All Priorities</option>
        {PRIORITIES.filter(Boolean).map((p) => (
          <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
        ))}
      </select>

      <select className="form-select" value={filters.status} onChange={handle("status")}>
        <option value="">All Statuses</option>
        {STATUSES.filter(Boolean).map((s) => (
          <option key={s} value={s}>{s.replace("_", " ")}</option>
        ))}
      </select>
    </div>
  );
}
