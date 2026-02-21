import { useState, useEffect } from "react";
import { Loader, BarChart3 } from "lucide-react";
import { ticketsApi } from "../api/tickets";

const PRIORITY_COLORS = {
  low: "#22c55e",
  medium: "#818cf8",
  high: "#f59e0b",
  critical: "#ef4444",
};

const CATEGORY_COLORS = {
  billing: "#38bdf8",
  technical: "#a78bfa",
  account: "#f472b6",
  general: "#6ee7b7",
};

function BreakdownRow({ label, count, total, color }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div className="breakdown-row">
      <span className="breakdown-key" style={{ color }}>{label}</span>
      <div className="breakdown-bar-wrap">
        <div className="breakdown-bar" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="breakdown-count">{count}</span>
    </div>
  );
}

export default function StatsDashboard({ refreshSignal }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    ticketsApi
      .stats()
      .then(({ data }) => setStats(data))
      .finally(() => setLoading(false));
  }, [refreshSignal]);

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: "3rem" }}>
        <Loader size={28} className="spinner" color="var(--accent)" />
      </div>
    );
  }

  if (!stats) return null;

  const totalPriority = Object.values(stats.priority_breakdown).reduce((a, b) => a + b, 0);
  const totalCategory = Object.values(stats.category_breakdown).reduce((a, b) => a + b, 0);

  return (
    <div>
      <div className="page-header">
        <div className="page-title" style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <BarChart3 size={22} color="var(--accent)" /> Dashboard
        </div>
        <div className="page-subtitle">Real-time aggregated metrics from the database.</div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Tickets</div>
          <div className="stat-value">{stats.total_tickets}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Open Tickets</div>
          <div className="stat-value accent">{stats.open_tickets}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Avg / Day</div>
          <div className="stat-value">{stats.avg_tickets_per_day}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Resolution Rate</div>
          <div className="stat-value">
            {stats.total_tickets > 0
              ? Math.round(((stats.total_tickets - stats.open_tickets) / stats.total_tickets) * 100)
              : 0}%
          </div>
        </div>
      </div>

      <div className="breakdown-grid">
        <div className="breakdown-card">
          <div className="breakdown-title">By Priority</div>
          {Object.entries(stats.priority_breakdown).map(([key, count]) => (
            <BreakdownRow key={key} label={key} count={count} total={totalPriority} color={PRIORITY_COLORS[key]} />
          ))}
        </div>
        <div className="breakdown-card">
          <div className="breakdown-title">By Category</div>
          {Object.entries(stats.category_breakdown).map(([key, count]) => (
            <BreakdownRow key={key} label={key} count={count} total={totalCategory} color={CATEGORY_COLORS[key]} />
          ))}
        </div>
      </div>
    </div>
  );
}
