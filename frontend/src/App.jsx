import { useState } from "react";
import { TicketPlus, List, BarChart3 } from "lucide-react";
import TicketForm from "./components/TicketForm";
import TicketList from "./components/TicketList";
import StatsDashboard from "./components/StatsDashboard";

const TABS = [
  { id: "list", label: "Tickets", icon: List },
  { id: "new", label: "New Ticket", icon: TicketPlus },
  { id: "stats", label: "Dashboard", icon: BarChart3 },
];

export default function App() {
  const [activeTab, setActiveTab] = useState("list");
  // Increment to trigger re-fetch in list + stats after new ticket
  const [refreshSignal, setRefreshSignal] = useState(0);

  const handleTicketCreated = () => {
    setRefreshSignal((n) => n + 1);
    setActiveTab("list");
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-logo">
          <TicketPlus size={22} />
          SupportDesk
        </div>
        <nav className="nav">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              className={`nav-btn ${activeTab === id ? "active" : ""}`}
              onClick={() => setActiveTab(id)}
            >
              <Icon size={15} />
              {label}
            </button>
          ))}
        </nav>
      </header>

      <main className="main">
        {activeTab === "new" && (
          <TicketForm onTicketCreated={handleTicketCreated} />
        )}
        {activeTab === "list" && (
          <TicketList refreshSignal={refreshSignal} />
        )}
        {activeTab === "stats" && (
          <StatsDashboard refreshSignal={refreshSignal} />
        )}
      </main>
    </div>
  );
}
