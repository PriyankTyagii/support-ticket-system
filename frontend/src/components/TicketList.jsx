import { useState, useEffect, useCallback } from "react";
import { Loader } from "lucide-react";
import { ticketsApi } from "../api/tickets";
import FilterBar from "./FilterBar";
import TicketCard from "./TicketCard";

const INITIAL_FILTERS = { search: "", category: "", priority: "", status: "" };

export default function TicketList({ refreshSignal }) {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState(INITIAL_FILTERS);

  const fetchTickets = useCallback(async () => {
    setLoading(true);
    try {
      const params = Object.fromEntries(
        Object.entries(filters).filter(([, v]) => v !== "")
      );
      const { data } = await ticketsApi.list(params);
      setTickets(data);
    } catch {
      // errors shown via toast from API layer
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets, refreshSignal]);

  const handleUpdated = (updated) => {
    setTickets((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
  };

  return (
    <div>
      <div className="page-header">
        <div className="page-title">All Tickets</div>
        <div className="page-subtitle">{tickets.length} ticket{tickets.length !== 1 ? "s" : ""} found</div>
      </div>

      <FilterBar filters={filters} onChange={setFilters} />

      {loading ? (
        <div style={{ display: "flex", justifyContent: "center", padding: "3rem" }}>
          <Loader size={28} className="spinner" color="var(--accent)" />
        </div>
      ) : tickets.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🎫</div>
          <div className="empty-state-title">No tickets found</div>
          <p>Try adjusting your filters or submit a new ticket.</p>
        </div>
      ) : (
        <div className="tickets-list">
          {tickets.map((ticket) => (
            <TicketCard key={ticket.id} ticket={ticket} onUpdated={handleUpdated} />
          ))}
        </div>
      )}
    </div>
  );
}
