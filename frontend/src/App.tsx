import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { api, type ClientSummary } from "./api/client";
import ClientCard from "./components/ClientCard";
import Dashboard from "./components/Dashboard";
import { Search, Wifi, WifiOff, BarChart3, Menu, X } from "lucide-react";

function App() {
  const [clients, setClients] = useState<ClientSummary[]>([]);
  const [selectedClientId, setSelectedClientId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    // Load clients
    api.getClients()
      .then(setClients)
      .catch((err) => console.error("Failed to load clients:", err));

    // Check health
    api.getHealth()
      .then((h) => setIsConnected(h.status === "ok"))
      .catch(() => setIsConnected(false));

    // Periodic health check
    const healthInterval = setInterval(() => {
      api.getHealth()
        .then((h) => setIsConnected(h.status === "ok"))
        .catch(() => setIsConnected(false));
    }, 30000);

    return () => clearInterval(healthInterval);
  }, []);

  const filteredClients = clients.filter((c) =>
    c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.occupation?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <AnimatePresence mode="wait">
        {sidebarOpen && (
          <motion.aside
            initial={{ x: -280, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -280, opacity: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="w-[280px] h-screen sticky top-0 flex-shrink-0 glass border-r border-[rgba(255,255,255,0.05)] flex flex-col shadow-[4px_0_24px_rgba(0,0,0,0.2)] z-20"
          >
            {/* Logo */}
            <div className="p-5 border-b border-[rgba(255,255,255,0.05)]">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl flex items-center justify-center"
                  style={{ background: "linear-gradient(135deg, var(--color-primary), var(--color-accent))" }}>
                  <BarChart3 size={16} className="text-white" />
                </div>
                <div>
                  <h1 className="text-base font-bold gradient-text">WealthVisor</h1>
                  <p className="text-[9px] text-[var(--color-primary-light)] font-mono uppercase tracking-widest mt-0.5">Agentic Intelligence</p>
                </div>
              </div>
            </div>

            {/* Search */}
            <div className="px-4 py-3">
              <div className="relative">
                <Search size={14} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-[var(--color-text-muted)]" />
                <input
                  type="text"
                  placeholder="Search clients..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 rounded-xl text-xs text-[var(--color-text)] placeholder-[var(--color-text-muted)] border border-[rgba(255,255,255,0.05)] focus:border-[var(--color-primary-light)] focus:outline-none transition-colors shadow-inner"
                  style={{ background: "rgba(0, 0, 0, 0.2)" }}
                />
              </div>
            </div>

            {/* All Clients button */}
            <div className="px-3">
              <button
                onClick={() => setSelectedClientId(null)}
                className={`w-full text-left px-3 py-2 rounded-xl text-xs font-medium transition-all ${
                  selectedClientId === null
                    ? "bg-[rgba(94,106,210,0.15)] text-[var(--color-primary-light)] shadow-sm"
                    : "text-[var(--color-text-secondary)] hover:bg-[rgba(255,255,255,0.03)]"
                }`}
              >
                All Clients ({clients.length})
              </button>
            </div>

            {/* Client List */}
            <div className="flex-1 overflow-y-auto px-2 py-2 space-y-0.5">
              {filteredClients.map((client) => (
                <ClientCard
                  key={client.id}
                  client={client}
                  isSelected={selectedClientId === client.id}
                  onClick={() => setSelectedClientId(selectedClientId === client.id ? null : client.id)}
                />
              ))}
            </div>

            {/* Connection Status */}
            <div className="p-4 border-t border-[rgba(255,255,255,0.05)]">
              <div className="flex items-center gap-2">
                {isConnected ? (
                  <>
                    <span className="w-2 h-2 rounded-full bg-emerald-400 pulse-dot" />
                    <span className="text-[10px] text-emerald-400 font-medium">Connected</span>
                    <Wifi size={11} className="text-emerald-400 ml-auto" />
                  </>
                ) : (
                  <>
                    <span className="w-2 h-2 rounded-full bg-red-400" />
                    <span className="text-[10px] text-red-400 font-medium">Disconnected</span>
                    <WifiOff size={11} className="text-red-400 ml-auto" />
                  </>
                )}
              </div>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <main className="flex-1 min-w-0">
        {/* Top Bar */}
        <header className="sticky top-0 z-10 glass border-b border-[rgba(255,255,255,0.05)] px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="w-8 h-8 rounded-lg flex items-center justify-center hover:bg-[rgba(255,255,255,0.05)] transition-colors"
            >
              {sidebarOpen ? <X size={16} className="text-[var(--color-text-muted)]" /> : <Menu size={16} className="text-[var(--color-text-muted)]" />}
            </button>
            <div>
              <h2 className="text-sm font-semibold text-[var(--color-text)]">
                {selectedClientId
                  ? clients.find((c) => c.id === selectedClientId)?.name || "Client"
                  : "Dashboard"}
              </h2>
              <p className="text-[10px] text-[var(--color-text-muted)]">
                {selectedClientId ? "Client View" : "Meeting Intelligence Overview"}
              </p>
            </div>
          </div>
          <div className="text-[10px] text-[var(--color-text-muted)]">
            {new Date().toLocaleDateString("en-IN", {
              weekday: "long",
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </div>
        </header>

        {/* Content */}
        <div className="p-6">
          <Dashboard selectedClientId={selectedClientId} />
        </div>
      </main>
    </div>
  );
}

export default App;
