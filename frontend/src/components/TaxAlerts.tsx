import { motion } from "framer-motion";
import { formatINR } from "../api/client";
import { TrendingDown, ArrowRight, Shield } from "lucide-react";

interface TaxAlertsProps {
  taxData: {
    harvest_opportunities?: any[];
    elss_recommendation?: any;
    tax_summary?: string;
    total_potential_tax_saving?: number;
    ltcg_tax_payable?: number;
    stcg_tax_payable?: number;
  };
}

export default function TaxAlerts({ taxData }: TaxAlertsProps) {
  const harvest = taxData?.harvest_opportunities || [];
  const elss = taxData?.elss_recommendation;
  const totalSaving = taxData?.total_potential_tax_saving || 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className="glass-card p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
          Tax Opportunities
        </h3>
        {totalSaving > 0 && (
          <motion.span
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 300, delay: 0.4 }}
            className="px-3 py-1 rounded-full text-xs font-bold"
            style={{
              background: "linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(16, 185, 129, 0.1))",
              color: "#6ee7b7",
              border: "1px solid rgba(16, 185, 129, 0.3)",
            }}
          >
            Est. Savings: {formatINR(totalSaving)}
          </motion.span>
        )}
      </div>

      {/* Tax Summary */}
      {taxData?.tax_summary && (
        <p className="text-sm text-[var(--color-text-secondary)] mb-4 leading-relaxed">
          {taxData.tax_summary}
        </p>
      )}

      {/* Harvest Opportunities */}
      <div className="space-y-4">
        {harvest.slice(0, 3).map((opp: any, i: number) => {
          // Fallback if backend didn't supply the keys (for older cached briefs)
          const lossAmount = opp.loss_amount || Math.abs(opp.unrealized_gain || 0);
          const estimatedSaving = opp.estimated_tax_saving || (lossAmount * (opp.holding_type === 'long_term' ? 0.10 : 0.15));
          
          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 + i * 0.1, type: "spring", stiffness: 300 }}
              className="flex items-center gap-4 p-4 rounded-2xl glass transition-all hover:bg-[rgba(252,91,101,0.02)] border border-[rgba(252,91,101,0.1)] hover:border-[rgba(252,91,101,0.25)]"
            >
              <div className="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-[rgba(252,91,101,0.15)] to-[rgba(252,91,101,0.05)] shadow-[0_0_15px_rgba(252,91,101,0.1)]">
                <TrendingDown size={18} className="text-red-400" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-baseline gap-2">
                    <span className="font-bold text-sm tracking-wide text-[var(--color-text)]">
                      {(opp.ticker || "").replace(".NS", "")}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-[rgba(255,255,255,0.05)] text-[var(--color-text-secondary)]">
                      {opp.holding_type === "long_term" ? "LTCL" : "STCL"}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[rgba(26,226,150,0.1)] border border-[rgba(26,226,150,0.2)]">
                    <span className="text-[11px] font-semibold text-emerald-400">
                      Save {formatINR(estimatedSaving)}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
                  <span>Book {formatINR(lossAmount)} loss</span>
                  <ArrowRight size={12} className="opacity-50" />
                  <span>Offset actionable gains</span>
                </div>
              </div>
            </motion.div>
          );
        })}

        {/* ELSS */}
        {elss && (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.6, type: "spring", stiffness: 300 }}
            className="flex items-center gap-4 p-4 rounded-2xl glass transition-all hover:bg-[rgba(94,106,210,0.02)] border border-[rgba(94,106,210,0.1)] hover:border-[rgba(94,106,210,0.25)] mt-4"
          >
            <div className="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-[rgba(94,106,210,0.2)] to-[rgba(94,106,210,0.05)] shadow-[0_0_15px_rgba(94,106,210,0.1)]">
              <Shield size={18} className="text-indigo-400" />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <span className="font-bold text-sm tracking-wide text-[var(--color-text)]">Section 80C / ELSS</span>
                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[rgba(26,226,150,0.1)] border border-[rgba(26,226,150,0.2)]">
                  <span className="text-[11px] font-semibold text-emerald-400">
                    Save {formatINR(elss.estimated_tax_saving)}
                  </span>
                </div>
              </div>
              <p className="text-xs text-[var(--color-text-muted)]">
                Invest {formatINR(elss.recommended_amount)} in <span className="text-[var(--color-text-secondary)] font-medium">{elss.suggested_fund}</span>
              </p>
            </div>
          </motion.div>
        )}

        {harvest.length === 0 && !elss && (
          <p className="text-sm text-[var(--color-text-muted)] text-center py-4">
            No immediate tax optimization opportunities identified.
          </p>
        )}
      </div>
    </motion.div>
  );
}
