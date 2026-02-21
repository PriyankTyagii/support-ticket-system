import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { ticketsApi } from "../api/tickets";
import toast from "react-hot-toast";

const STATUS_FLOW = ["open", "in_progress", "resolved", "closed"];

function formatDate(iso) {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function TicketCard({ ticket, onUpdated }) {
  const [expanded, setExpanded] = useState(false);
  const [updating, setUpdating] = useState(false);

  const handleStatusChange = async (e) => {
    const newStatus = e.target.value;
    setUpdating(true);
    try {
      const { data } = await ticketsApi.update(ticket.id, { status: newStatus });
      onUpdated(data);
      toast.success("Status updated.");
    } catch {
      toast.error("Failed to update status.");
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div
      className={`ticket-card ${expanded ? "expanded" : ""}`}
      onClick={() => setExpanded((v) => !v)}
    >
      <div className="ticket-card-header">
        <div className="ticket-title">{ticket.title}</div>
        <div className="ticket-meta">
          <span className={`badge badge-priority-${ticket.priority}`}>{ticket.priority}</span>
          <span className={`badge badge-status-${ticket.status}`}>{ticket.status.replace("_", " ")}</span>
          <span className="badge badge-category">{ticket.category}</span>
          {expanded ? <ChevronUp size={16} color="var(--text-muted)" /> : <ChevronDown size={16} color="var(--text-muted)" />}
        </div>
      </div>

      <div className="ticket-description">
        {expanded ? ticket.description : ticket.description.slice(0, 160) + (ticket.description.length > 160 ? "…" : "")}
      </div>

      <div className="ticket-footer">
        <span className="ticket-time">#{ticket.id} · {formatDate(ticket.created_at)}</span>
      </div>

      {expanded && (
        <div className="status-select-row" onClick={(e) => e.stopPropagation()}>
          <span className="status-select-label">Change Status:</span>
          <select
            className="status-select"
            value={ticket.status}
            onChange={handleStatusChange}
            disabled={updating}
          >
            {STATUS_FLOW.map((s) => (
              <option key={s} value={s}>{s.replace("_", " ")}</option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}
