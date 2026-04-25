/**
 * WealthVisor — API Client
 * All API calls to the FastAPI backend. No fetch() in components.
 */

const BASE = "http://localhost:8000";

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options);
  if (!res.ok) {
    throw new Error(`API Error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export interface ClientSummary {
  id: number;
  name: string;
  email: string;
  phone: string;
  age: number;
  occupation: string;
  risk_tolerance: string;
  investment_goal: string;
  aum: number;
  annual_income: number;
  tax_bracket: number;
  upcoming_meeting_count: number;
}

export interface Meeting {
  id: number;
  client_id: number;
  client_name: string;
  client_aum: number;
  client_risk: string;
  scheduled_at: string;
  duration_min: number;
  meeting_type: string;
  agenda_notes: string;
  brief_generated: boolean;
  brief_generated_at: string | null;
}

export interface DashboardStats {
  briefs_generated_today: number;
  avg_generation_time: number;
  total_tax_savings_identified: number;
  clients_high_behavioral_risk: number;
  active_meetings_today: number;
}

export interface BriefResponse {
  meeting_id: number;
  brief_content: any;
  brief_generated_at: string;
}

export const api = {
  getClients: () => fetchJSON<ClientSummary[]>(`${BASE}/clients`),

  getClient: (id: number) => fetchJSON<any>(`${BASE}/clients/${id}`),

  getMeetings: (upcomingOnly = true) =>
    fetchJSON<Meeting[]>(`${BASE}/meetings?upcoming_only=${upcomingOnly}`),

  getMeeting: (id: number) => fetchJSON<any>(`${BASE}/meetings/${id}`),

  generateBrief: (meetingId: number) =>
    fetchJSON<{ status: string; meeting_id: number }>(
      `${BASE}/meetings/${meetingId}/generate-brief`,
      { method: "POST" }
    ),

  getBrief: (meetingId: number) =>
    fetchJSON<BriefResponse>(`${BASE}/meetings/${meetingId}/brief`),

  getStats: () => fetchJSON<DashboardStats>(`${BASE}/stats`),

  getHealth: () => fetchJSON<any>(`${BASE}/health`),
};

/**
 * Format INR in Indian number system (lakhs/crores).
 */
export function formatINR(amount: number): string {
  if (Math.abs(amount) >= 10000000) {
    return `₹${(amount / 10000000).toFixed(1)} Cr`;
  }
  if (Math.abs(amount) >= 100000) {
    return `₹${(amount / 100000).toFixed(1)} L`;
  }
  return `₹${amount.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

/**
 * Time ago formatter.
 */
export function timeUntil(dateStr: string): string {
  const target = new Date(dateStr);
  const now = new Date();
  const diffMs = target.getTime() - now.getTime();
  const diffMins = Math.round(diffMs / 60000);

  if (diffMins < 0) return `${Math.abs(diffMins)} min ago`;
  if (diffMins < 60) return `in ${diffMins} min`;
  if (diffMins < 1440) return `in ${Math.round(diffMins / 60)} hr`;
  return `in ${Math.round(diffMins / 1440)} day`;
}
