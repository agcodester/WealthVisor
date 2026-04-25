import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { api, formatINR, timeUntil, type Meeting, type DashboardStats } from "../api/client";
import BriefViewer from "./BriefViewer";
import {
  FileText, Clock, DollarSign, AlertTriangle, Calendar,
  Zap, Eye, Loader2, Sparkles
} from "lucide-react";

interface DashboardProps {
  selectedClientId: number | null;
}

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  glowClass: string;
  delay: number;
}

function StatCard({ title, value, icon, glowClass, delay }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      className={`glass-card p-4 ${glowClass}`}
    >
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-[rgba(255,255,255,0.08)] to-[rgba(255,255,255,0.02)] shadow-inner">
          {icon}
        </div>
        <div>
          <p className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider font-medium">{title}</p>
          <p className="text-lg font-bold text-[var(--color-text)]">{value}</p>
        </div>
      </div>
    </motion.div>
  );
}

export default function Dashboard({ selectedClientId }: DashboardProps) {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [activeBrief, setActiveBrief] = useState<any>(null);
  const [generatingId, setGeneratingId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    try {
      const [meetingsData, statsData] = await Promise.all([
        api.getMeetings(true),
        api.getStats(),
      ]);
      setMeetings(meetingsData);
      setStats(statsData);
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 15000); // refresh every 15s
    return () => clearInterval(interval);
  }, [loadData]);

  const handleGenerateBrief = async (meetingId: number) => {
    setGeneratingId(meetingId);
    try {
      await api.generateBrief(meetingId);
      // Poll every 3 seconds until brief is ready
      const poll = setInterval(async () => {
        try {
          const result = await api.getBrief(meetingId);
          if (result?.brief_content) {
            clearInterval(poll);
            setGeneratingId(null);
            setActiveBrief(result.brief_content);
            loadData();
          }
        } catch {
          // Brief not ready yet — keep polling
        }
      }, 3000);

      // Safety timeout: stop polling after 3 minutes
      setTimeout(() => {
        clearInterval(poll);
        setGeneratingId(null);
      }, 180000);
    } catch (err) {
      console.error("Failed to generate brief:", err);
      setGeneratingId(null);
    }
  };

  const handleViewBrief = async (meetingId: number) => {
    try {
      const result = await api.getBrief(meetingId);
      if (result?.brief_content) {
        setActiveBrief(result.brief_content);
      }
    } catch (err) {
      console.error("Failed to load brief:", err);
    }
  };

  if (activeBrief) {
    return (
      <div>
        <motion.button
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          onClick={() => setActiveBrief(null)}
          className="mb-4 text-sm text-[var(--color-primary-light)] hover:text-[var(--color-primary)] transition-colors flex items-center gap-1"
        >
          ← Back to Dashboard
        </motion.button>
        <BriefViewer brief={activeBrief} />
      </div>
    );
  }

  const filteredMeetings = selectedClientId
    ? meetings.filter((m) => m.client_id === selectedClientId)
    : meetings;

  return (
    <div className="space-y-6">
      {/* Stats Row */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
          <StatCard
            title="Briefs Today"
            value={stats.briefs_generated_today}
            icon={<FileText size={18} className="text-[var(--color-primary-light)]" />}
            glowClass="stat-glow-purple"
            delay={0}
          />
          <StatCard
            title="Avg Gen Time"
            value={`${stats.avg_generation_time}s`}
            icon={<Clock size={18} className="text-[var(--color-accent)]" />}
            glowClass="stat-glow-blue"
            delay={0.05}
          />
          <StatCard
            title="Tax Savings"
            value={formatINR(stats.total_tax_savings_identified)}
            icon={<DollarSign size={18} className="text-emerald-400" />}
            glowClass="stat-glow-green"
            delay={0.1}
          />
          <StatCard
            title="High Risk Clients"
            value={stats.clients_high_behavioral_risk}
            icon={<AlertTriangle size={18} className="text-amber-400" />}
            glowClass="stat-glow-gold"
            delay={0.15}
          />
          <StatCard
            title="Meetings Today"
            value={stats.active_meetings_today}
            icon={<Calendar size={18} className="text-rose-400" />}
            glowClass="stat-glow-red"
            delay={0.2}
          />
        </div>
      )}

      {/* Upcoming Meetings */}
      <div>
        <h2 className="text-sm font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider mb-3 flex items-center gap-2">
          <Sparkles size={14} className="text-[var(--color-primary-light)]" />
          Upcoming Meetings
        </h2>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="glass-card p-5 h-36 shimmer rounded-2xl" />
            ))}
          </div>
        ) : filteredMeetings.length === 0 ? (
          <div className="glass-card p-8 text-center">
            <Calendar size={40} className="text-[var(--color-text-muted)] mx-auto mb-3" />
            <p className="text-sm text-[var(--color-text-muted)]">No upcoming meetings</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <AnimatePresence>
              {filteredMeetings.map((meeting, i) => (
                <motion.div
                  key={meeting.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.4, delay: i * 0.05 }}
                  className="glass-card p-5 group"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="text-base font-bold text-[var(--color-text)]">{meeting.client_name}</h3>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-[10px] px-2 py-0.5 rounded-md bg-[rgba(255,255,255,0.05)] text-[var(--color-primary-light)] font-mono">
                          {(meeting.meeting_type || "review").replace("_", " ")}
                        </span>
                        <span className="text-xs text-[var(--color-text-muted)]">{meeting.duration_min} min</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-xs font-semibold text-[var(--color-accent)]">
                        {timeUntil(meeting.scheduled_at)}
                      </p>
                      <p className="text-[10px] text-[var(--color-text-muted)] mt-0.5">
                        {new Date(meeting.scheduled_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-xs text-[var(--color-text-secondary)]">
                      AUM: {formatINR(meeting.client_aum || 0)}
                    </span>

                    {meeting.brief_generated ? (
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => handleViewBrief(meeting.id)}
                        className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all"
                        style={{
                          background: "linear-gradient(135deg, rgba(26, 226, 150, 0.15), rgba(26, 226, 150, 0.05))",
                          color: "#1AE296",
                          border: "1px solid rgba(26, 226, 150, 0.3)",
                        }}
                      >
                        <Eye size={13} />
                        View Brief
                      </motion.button>
                    ) : generatingId === meeting.id ? (
                      <span className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold text-[var(--color-accent)]">
                        <Loader2 size={13} className="animate-spin" />
                        Generating...
                      </span>
                    ) : (
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => handleGenerateBrief(meeting.id)}
                        className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all"
                        style={{
                          background: "linear-gradient(135deg, var(--color-primary), var(--color-primary-dark))",
                          boxShadow: "0 4px 12px rgba(94, 106, 210, 0.3)",
                        }}
                      >
                        <Zap size={13} />
                        Generate Brief
                      </motion.button>
                    )}
                  </div>

                  {meeting.agenda_notes && (
                    <p className="text-[11px] text-[var(--color-text-muted)] mt-2 line-clamp-2 leading-relaxed">
                      {meeting.agenda_notes}
                    </p>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>
    </div>
  );
}
