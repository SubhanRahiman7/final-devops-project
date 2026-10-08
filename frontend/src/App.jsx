import { useCallback, useEffect, useState } from "react";
import { api } from "./api.js";
import ActivityFeed from "./components/ActivityFeed.jsx";
import Kpis from "./components/Kpis.jsx";
import Pipeline from "./components/Pipeline.jsx";
import Sidebar from "./components/Sidebar.jsx";
import TicketModal from "./components/TicketModal.jsx";
import TicketTable from "./components/TicketTable.jsx";

const FILTERS = [
  ["all", "All"],
  ["open", "Open"],
  ["in_progress", "In progress"],
  ["resolved", "Resolved"],
];
const NEXT_STATUS = { open: "in_progress", in_progress: "resolved", resolved: "open" };

export default function App() {
  const [tickets, setTickets] = useState([]);
  const [stats, setStats] = useState(null);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showModal, setShowModal] = useState(false);

  const load = useCallback(async () => {
    try {
      const [list, summary] = await Promise.all([api.listTickets(filter), api.stats()]);
      setTickets(list);
      setStats(summary);
      setError("");
    } catch (err) {
      setError(`Cannot reach the backend: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    setLoading(true);
    load();
    const timer = setInterval(load, 15000);
    return () => clearInterval(timer);
  }, [load]);

  const run = (action) => async (...args) => {
    try {
      await action(...args);
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="shell">
      <Sidebar />
      <main className="content">
        <header className="topbar">
          <div>
            <h1>Support dashboard</h1>
            <p className="muted">Track, prioritise and resolve customer tickets.</p>
          </div>
          <button className="btn" onClick={() => setShowModal(true)}>+ New ticket</button>
        </header>

        {error && <div className="banner">{error} <button className="link" onClick={load}>Retry</button></div>}
        {loading && !stats && <p className="muted">Loading...</p>}
        {stats && <Kpis stats={stats} />}

        <div className="grid">
          <section className="panel wide">
            <div className="filters" role="tablist">
              {FILTERS.map(([key, label]) => (
                <button key={key} className={filter === key ? "chip active" : "chip"} onClick={() => setFilter(key)}>
                  {label}
                </button>
              ))}
            </div>
            <TicketTable
              tickets={tickets}
              onAdvance={run((t) => api.updateTicket(t.id, { status: NEXT_STATUS[t.status] }))}
              onDelete={run((t) => api.deleteTicket(t.id))}
            />
          </section>
          <div className="side">
            <ActivityFeed tickets={tickets} />
            <Pipeline />
          </div>
        </div>
      </main>
      {showModal && (
        <TicketModal onClose={() => setShowModal(false)} onCreate={run(api.createTicket)} />
      )}
    </div>
  );
}
