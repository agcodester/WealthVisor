import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Tooltip,
} from "recharts";
import { motion } from "framer-motion";

interface BehavioralRadarProps {
  scores: Record<string, number>;
}

const DIMENSION_LABELS: Record<string, string> = {
  loss_aversion: "Loss Aversion",
  overconfidence: "Overconfidence",
  herding: "Herding",
  recency_bias: "Recency Bias",
  anchoring: "Anchoring",
  status_quo: "Status Quo",
};

export default function BehavioralRadar({ scores }: BehavioralRadarProps) {
  const data = Object.entries(scores).map(([key, value]) => ({
    dimension: DIMENSION_LABELS[key] || key,
    score: value,
    fullMark: 10,
  }));

  if (data.length === 0) return null;

  const maxScore = Math.max(...data.map((d) => d.score));
  const riskLevel = maxScore > 7 ? "High Risk" : maxScore > 4 ? "Moderate" : "Low Risk";
  const riskColor = maxScore > 7 ? "#ef4444" : maxScore > 4 ? "#f59e0b" : "#10b981";

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, delay: 0.1 }}
      className="glass-card p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
          Behavioral Profile
        </h3>
        <span
          className="px-3 py-1 rounded-full text-xs font-semibold"
          style={{
            background: `${riskColor}20`,
            color: riskColor,
            border: `1px solid ${riskColor}40`,
          }}
        >
          {riskLevel}
        </span>
      </div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={data} cx="50%" cy="50%" outerRadius="70%">
            <PolarGrid stroke="rgba(99, 102, 241, 0.15)" />
            <PolarAngleAxis
              dataKey="dimension"
              tick={{ fill: "#94a3b8", fontSize: 11 }}
            />
            <PolarRadiusAxis
              angle={30}
              domain={[0, 10]}
              tick={{ fill: "#64748b", fontSize: 10 }}
            />
            <Radar
              name="Score"
              dataKey="score"
              stroke="#6366f1"
              fill="#6366f1"
              fillOpacity={0.25}
              animationDuration={800}
            />
            <Tooltip
              contentStyle={{
                background: "rgba(15, 23, 42, 0.95)",
                border: "1px solid rgba(99, 102, 241, 0.2)",
                borderRadius: "12px",
                color: "#f1f5f9",
                fontSize: "0.875rem",
              }}
              formatter={(value: any) => [`${value}/10`, "Score"]}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
