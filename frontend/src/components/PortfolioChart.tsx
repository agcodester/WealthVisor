import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";
import { motion } from "framer-motion";

interface PortfolioChartProps {
  allocation: Record<string, number>;
}

const COLORS: Record<string, string> = {
  equity: "#6366f1",
  etf: "#22d3ee",
  bond_fund: "#10b981",
  gold: "#fbbf24",
  cash: "#94a3b8",
  commodities: "#f59e0b",
  other: "#64748b",
};

export default function PortfolioChart({ allocation }: PortfolioChartProps) {
  const data = Object.entries(allocation).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1).replace("_", " "),
    value: Number(value.toFixed(1)),
    color: COLORS[name] || COLORS.other,
  }));

  if (data.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="glass-card p-6"
    >
      <h3 className="text-sm font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider mb-4">
        Asset Allocation
      </h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={90}
              paddingAngle={3}
              dataKey="value"
              animationBegin={0}
              animationDuration={800}
              animationEasing="ease-out"
            >
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.color} stroke="transparent" />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                background: "rgba(15, 23, 42, 0.95)",
                border: "1px solid rgba(99, 102, 241, 0.2)",
                borderRadius: "12px",
                color: "#f1f5f9",
                fontSize: "0.875rem",
              }}
              formatter={(value: any) => [`${value}%`, ""]}
            />
            <Legend
              verticalAlign="bottom"
              height={36}
              iconSize={10}
              iconType="circle"
              formatter={(value) => (
                <span style={{ color: "#94a3b8", fontSize: "0.75rem" }}>{value}</span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
