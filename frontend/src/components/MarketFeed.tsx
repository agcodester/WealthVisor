import { motion } from "framer-motion";
import { ExternalLink } from "lucide-react";

interface MarketFeedProps {
  news: any[];
  alerts: any[];
  macroSummary: string;
}

function SentimentDot({ score }: { score: number }) {
  const color = score < -0.3 ? "#ef4444" : score > 0.3 ? "#10b981" : "#64748b";
  return (
    <span
      className="inline-block w-2 h-2 rounded-full flex-shrink-0"
      style={{ background: color, boxShadow: `0 0 6px ${color}60` }}
    />
  );
}

export default function MarketFeed({ news, alerts, macroSummary }: MarketFeedProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.15 }}
      className="glass-card p-6"
    >
      <h3 className="text-sm font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider mb-4">
        Market Intelligence
      </h3>

      {/* Macro Summary */}
      {macroSummary && (
        <div className="mb-4 p-3 rounded-xl" style={{ background: "rgba(59, 130, 246, 0.08)", border: "1px solid rgba(59, 130, 246, 0.15)" }}>
          <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed">{macroSummary}</p>
        </div>
      )}

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="mb-4 space-y-2">
          {alerts.slice(0, 4).map((alert: any, i: number) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 + i * 0.08 }}
              className={`px-3 py-2 rounded-lg text-xs ${
                alert.severity === "high"
                  ? "badge-high"
                  : alert.severity === "medium"
                  ? "badge-medium"
                  : "badge-low"
              }`}
            >
              <span className="font-semibold">{(alert.ticker || "").replace(".NS", "")}</span>
              <span className="mx-1">·</span>
              <span>{alert.description}</span>
            </motion.div>
          ))}
        </div>
      )}

      {/* News Feed */}
      <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
        {news.slice(0, 8).map((article: any, i: number) => (
          <motion.a
            key={i}
            href={article.url || "#"}
            target="_blank"
            rel="noopener noreferrer"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 + i * 0.05 }}
            className="flex items-start gap-2 p-2 rounded-lg transition-colors duration-200 group"
            style={{ background: "transparent" }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(99, 102, 241, 0.05)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
          >
            <SentimentDot score={article.sentiment_score || 0} />
            <div className="flex-1 min-w-0">
              <p className="text-xs text-[var(--color-text)] leading-snug line-clamp-2 group-hover:text-[var(--color-primary-light)] transition-colors">
                {article.title}
              </p>
              <p className="text-[10px] text-[var(--color-text-muted)] mt-0.5">
                {article.source} · {article.sentiment_score?.toFixed(2) || "0.00"}
              </p>
            </div>
            <ExternalLink size={10} className="text-[var(--color-text-muted)] flex-shrink-0 mt-1 opacity-0 group-hover:opacity-100 transition-opacity" />
          </motion.a>
        ))}
        {news.length === 0 && (
          <p className="text-sm text-[var(--color-text-muted)] text-center py-4">No recent news available.</p>
        )}
      </div>
    </motion.div>
  );
}
