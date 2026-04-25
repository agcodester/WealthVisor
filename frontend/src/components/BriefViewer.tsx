import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { formatINR } from "../api/client";
import PortfolioChart from "./PortfolioChart";
import BehavioralRadar from "./BehavioralRadar";
import TaxAlerts from "./TaxAlerts";
import MarketFeed from "./MarketFeed";
import {
  ChevronDown, ChevronUp, FileText, PieChart, Brain,
  BarChart3, MessageSquare, Mail, Calendar,
  Clock, AlertTriangle
} from "lucide-react";

interface BriefViewerProps {
  brief: any;
  onClose?: () => void;
}

interface SectionProps {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  defaultOpen?: boolean;
  delay?: number;
}

function CollapsibleSection({ title, icon, children, defaultOpen = true, delay = 0 }: SectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      className="glass-card overflow-hidden"
    >
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 hover:bg-[rgba(255,255,255,0.02)] transition-colors"
      >
        <div className="flex items-center gap-2.5">
          <span className="text-[var(--color-primary-light)]">{icon}</span>
          <span className="text-sm font-semibold text-[var(--color-text)]">{title}</span>
        </div>
        {isOpen ? (
          <ChevronUp size={16} className="text-[var(--color-text-muted)]" />
        ) : (
          <ChevronDown size={16} className="text-[var(--color-text-muted)]" />
        )}
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default function BriefViewer({ brief }: BriefViewerProps) {
  if (!brief) return null;

  const meta = brief.metadata || {};
  const portfolio = brief.portfolio || {};
  const perf = portfolio.performance || {};
  const market = brief.market_intelligence || {};
  const tax = brief.tax_opportunities || {};
  const behavioral = brief.behavioral_intelligence || {};
  const research = brief.macro_research || {};

  return (
    <div className="space-y-4">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-6"
      >
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xl font-bold gradient-text">
            📋 Meeting Brief: {meta.client_name}
          </h2>
          <span className="text-xs text-[var(--color-text-muted)] flex items-center gap-1">
            <Clock size={12} />
            {brief.generation_time_sec?.toFixed(1)}s
          </span>
        </div>
        <div className="flex items-center gap-3 text-xs text-[var(--color-text-secondary)]">
          <span className="px-2 py-1 rounded-lg bg-[rgba(255,255,255,0.05)] text-[var(--color-primary-light)] font-mono">
            {(meta.meeting_type || "review").replace("_", " ").toUpperCase()}
          </span>
          <span className="flex items-center gap-1">
            <Calendar size={12} />
            {meta.meeting_at ? new Date(meta.meeting_at).toLocaleString("en-IN") : ""}
          </span>
          <span>AUM: {formatINR(meta.advisor_aum_this_client || 0)}</span>
        </div>
      </motion.div>

      {/* Executive Summary */}
      <CollapsibleSection title="Executive Summary" icon={<FileText size={16} />} delay={0.05}>
        <p className="text-sm text-[var(--color-text)] leading-relaxed">
          {brief.executive_summary || "Generating..."}
        </p>
      </CollapsibleSection>

      {/* Portfolio + Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <CollapsibleSection title="Portfolio Snapshot" icon={<PieChart size={16} />} delay={0.1}>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 rounded-xl bg-gradient-to-br from-[rgba(255,255,255,0.05)] to-[rgba(255,255,255,0.01)] border border-[rgba(255,255,255,0.03)]">
                <p className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-widest font-mono">Total Value</p>
                <p className="text-lg font-bold text-[var(--color-text)]">{formatINR(portfolio.total_value || 0)}</p>
              </div>
              <div className="p-3 rounded-xl bg-gradient-to-br from-[rgba(255,255,255,0.05)] to-[rgba(255,255,255,0.01)] border border-[rgba(255,255,255,0.03)]">
                <p className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-widest font-mono">30d Return</p>
                <p className={`text-lg font-bold ${(perf.return_30d || 0) >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                  {(perf.return_30d || 0) >= 0 ? "+" : ""}{perf.return_30d || 0}%
                </p>
              </div>
              <div className="p-3 rounded-xl bg-gradient-to-br from-[rgba(255,255,255,0.05)] to-[rgba(255,255,255,0.01)] border border-[rgba(255,255,255,0.03)]">
                <p className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-widest font-mono">vs NIFTY 50</p>
                <p className={`text-lg font-bold ${(perf.vs_nifty_30d || 0) >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                  {(perf.vs_nifty_30d || 0) >= 0 ? "+" : ""}{perf.vs_nifty_30d || 0}%
                </p>
              </div>
              <div className="p-3 rounded-xl bg-gradient-to-br from-[rgba(255,255,255,0.05)] to-[rgba(255,255,255,0.01)] border border-[rgba(255,255,255,0.03)]">
                <p className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-widest font-mono">YTD Return</p>
                <p className={`text-lg font-bold ${(perf.ytd_return || 0) >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                  {(perf.ytd_return || 0) >= 0 ? "+" : ""}{perf.ytd_return || 0}%
                </p>
              </div>
            </div>

            {/* Top Holdings Table */}
            {(portfolio.top_holdings || []).length > 0 && (
              <div className="mt-2">
                <p className="text-[10px] text-[var(--color-text-muted)] uppercase mb-2 font-semibold">Top Holdings</p>
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-[var(--color-text-muted)]">
                      <th className="text-left pb-1.5">Ticker</th>
                      <th className="text-right pb-1.5">Value</th>
                      <th className="text-right pb-1.5">Weight</th>
                      <th className="text-right pb-1.5">30d</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(portfolio.top_holdings || []).map((h: any, i: number) => (
                      <tr key={i} className="border-t border-[var(--color-surface-3)]">
                        <td className="py-1.5 font-semibold">{(h.ticker || "").replace(".NS", "")}</td>
                        <td className="text-right text-[var(--color-text-secondary)]">{formatINR(h.current_value || 0)}</td>
                        <td className="text-right text-[var(--color-text-secondary)]">{((h.actual_weight || 0) * 100).toFixed(1)}%</td>
                        <td className={`text-right font-medium ${(h.return_30d || 0) >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                          {(h.return_30d || 0) >= 0 ? "+" : ""}{h.return_30d || 0}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </CollapsibleSection>

        <PortfolioChart allocation={portfolio.asset_allocation || {}} />
      </div>

      {/* Market + Behavioral Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <MarketFeed
          news={market.relevant_news || []}
          alerts={market.alerts || []}
          macroSummary={market.macro_summary || ""}
        />
        <BehavioralRadar scores={behavioral.risk_profile || {}} />
      </div>

      {/* Tax + Coaching Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <TaxAlerts taxData={tax} />

        <CollapsibleSection title="Coaching Points" icon={<Brain size={16} />} delay={0.25}>
          <div className="space-y-3">
            {(behavioral.coaching_points || []).map((point: string, i: number) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 + i * 0.1 }}
                className="flex gap-3 p-3 rounded-xl"
                style={{ background: "rgba(94, 106, 210, 0.05)", border: "1px solid rgba(94, 106, 210, 0.15)" }}
              >
                <span className="text-sm font-bold text-[var(--color-primary-light)] flex-shrink-0">{i + 1}.</span>
                <p className="text-xs text-[var(--color-text-secondary)] leading-relaxed">{point}</p>
              </motion.div>
            ))}
            {/* Flags */}
            {(behavioral.flags || []).length > 0 && (
              <div className="mt-2 space-y-1.5">
                <p className="text-[10px] text-[var(--color-text-muted)] uppercase font-semibold flex items-center gap-1">
                  <AlertTriangle size={10} /> Behavioral Flags
                </p>
                {(behavioral.flags || []).map((flag: string, i: number) => (
                  <p key={i} className="text-xs text-amber-300/80 pl-3 border-l-2 border-amber-400/30">
                    {flag}
                  </p>
                ))}
              </div>
            )}
          </div>
        </CollapsibleSection>
      </div>

      {/* Sector Research */}
      <CollapsibleSection title="Sector & Macro Research" icon={<BarChart3 size={16} />} delay={0.3}>
        <div className="space-y-2">
          {Object.entries(research.sector_outlook || {}).map(([sector, outlook], i) => (
            <div key={i} className="flex gap-2 text-xs">
              <span className="font-semibold text-[var(--color-primary-light)] w-24 flex-shrink-0">{sector}</span>
              <span className="text-[var(--color-text-secondary)] leading-relaxed">{String(outlook)}</span>
            </div>
          ))}
          {(research.key_indicators || []).length > 0 && (
            <div className="mt-3 pt-3 border-t border-[var(--color-surface-3)] space-y-1.5">
              <p className="text-[10px] text-[var(--color-text-muted)] uppercase font-semibold">Key Indicators</p>
              {(research.key_indicators || []).map((ind: any, i: number) => (
                <p key={i} className="text-xs text-[var(--color-text-secondary)]">
                  <span className="font-medium text-[var(--color-text)]">{ind.title}</span> — {ind.summary}
                </p>
              ))}
            </div>
          )}
        </div>
      </CollapsibleSection>

      {/* Agenda + Talking Points */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <CollapsibleSection title="Meeting Agenda" icon={<Calendar size={16} />} delay={0.35}>
          <div className="space-y-2">
            {(brief.suggested_agenda || []).map((item: string, i: number) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + i * 0.05 }}
                className="flex items-start gap-2 text-xs text-[var(--color-text-secondary)]"
              >
                <span className="w-5 h-5 rounded-full bg-[rgba(94,106,210,0.15)] text-[var(--color-primary-light)] flex items-center justify-center text-[10px] font-bold flex-shrink-0 mt-0.5">
                  {i + 1}
                </span>
                <span className="leading-relaxed">{item}</span>
              </motion.div>
            ))}
          </div>
        </CollapsibleSection>

        <CollapsibleSection title="Talking Points" icon={<MessageSquare size={16} />} delay={0.4}>
          <div className="space-y-2.5">
            {(brief.talking_points || []).map((point: string, i: number) => (
              <div key={i} className="flex items-start gap-2 text-xs text-[var(--color-text-secondary)]">
                <span className="text-[var(--color-accent)] font-bold flex-shrink-0">{i + 1}.</span>
                <span className="leading-relaxed">{point}</span>
              </div>
            ))}
          </div>
        </CollapsibleSection>
      </div>

      {/* Follow-up Email */}
      <CollapsibleSection title="Draft Follow-Up Email" icon={<Mail size={16} />} defaultOpen={false} delay={0.45}>
        <div className="p-4 rounded-xl bg-[rgba(15,23,42,0.5)] text-xs text-[var(--color-text-secondary)] leading-relaxed whitespace-pre-line font-mono">
          {brief.draft_follow_up_email || "Email draft will be generated."}
        </div>
      </CollapsibleSection>

      {/* Footer */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="text-center text-[10px] text-[var(--color-text-muted)] py-4"
      >
        Generated by WealthVisor · {meta.generated_at ? new Date(meta.generated_at).toLocaleString("en-IN") : ""} · {brief.generation_time_sec?.toFixed(1)}s
      </motion.div>
    </div>
  );
}
