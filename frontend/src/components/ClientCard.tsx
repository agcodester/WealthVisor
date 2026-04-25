import { motion } from "framer-motion";
import { formatINR } from "../api/client";
import { TrendingUp, Calendar } from "lucide-react";

interface ClientCardProps {
  client: {
    id: number;
    name: string;
    occupation?: string;
    aum: number;
    risk_tolerance: string;
    investment_goal?: string;
    upcoming_meeting_count?: number;
  };
  onClick?: () => void;
  isSelected?: boolean;
}

const RISK_COLORS: Record<string, string> = {
  conservative: "#1AE296",
  moderate: "#FFB340",
  aggressive: "#FC5B65",
};

export default function ClientCard({ client, onClick, isSelected }: ClientCardProps) {
  const riskColor = RISK_COLORS[client.risk_tolerance] || "#64748b";

  return (
    <motion.button
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
      onClick={onClick}
      className={`w-full text-left p-3.5 rounded-xl transition-all duration-300 ${
        isSelected
          ? "bg-[rgba(94,106,210,0.15)] border border-[rgba(94,106,210,0.3)] shadow-[0_0_15px_rgba(94,106,210,0.1)]"
          : "bg-transparent border border-transparent hover:bg-[rgba(255,255,255,0.03)] hover:border-[rgba(255,255,255,0.05)]"
      }`}
    >
      <div className="flex items-center gap-3">
        <div
          className="w-9 h-9 rounded-xl flex items-center justify-center text-sm font-bold flex-shrink-0"
          style={{
            background: `${riskColor}18`,
            color: riskColor,
          }}
        >
          {client.name.charAt(0)}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-[var(--color-text)] truncate">{client.name}</p>
          <p className="text-[11px] text-[var(--color-text-muted)] truncate">{client.occupation || ""}</p>
        </div>
      </div>
      <div className="flex items-center gap-3 mt-2 ml-12">
        <span className="text-xs text-[var(--color-text-secondary)] flex items-center gap-1">
          <TrendingUp size={10} />
          {formatINR(client.aum)}
        </span>
        <span
          className="text-[10px] font-semibold px-2 py-0.5 rounded-full"
          style={{
            background: `${riskColor}18`,
            color: riskColor,
            border: `1px solid ${riskColor}30`,
          }}
        >
          {client.risk_tolerance}
        </span>
        {(client.upcoming_meeting_count || 0) > 0 && (
          <span className="text-[10px] text-[var(--color-accent)] flex items-center gap-0.5">
            <Calendar size={10} />
            {client.upcoming_meeting_count}
          </span>
        )}
      </div>
    </motion.button>
  );
}
