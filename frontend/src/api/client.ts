// Usar VITE_API_URL si está configurado, sino intentar localhost primero (mejor para Windows)
const API_BASE = import.meta.env.VITE_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

const TOKEN_KEY = "mediflow_token";
const USER_KEY = "mediflow_user";

export type UserProfile = {
  id: string;
  email: string;
  display_name: string | null;
  photo_url: string | null;
  role: "patient" | "admin";
  created_at: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
  user: UserProfile;
};

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export function getStoredUser(): UserProfile | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as UserProfile;
  } catch {
    return null;
  }
}

export function setSession(tr: TokenResponse) {
  setToken(tr.access_token);
  localStorage.setItem(USER_KEY, JSON.stringify(tr.user));
}

export function clearSession() {
  setToken(null);
  localStorage.removeItem(USER_KEY);
}

async function request<T>(
  path: string,
  options: RequestInit & { json?: unknown } = {}
): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  let body: BodyInit | undefined = options.body as BodyInit | undefined;
  if (options.json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(options.json);
  }
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers, body });
  if (res.status === 204) return undefined as T;
  const text = await res.text();
  if (!res.ok) {
    let message = text;
    try {
      const j = JSON.parse(text) as { detail?: unknown };
      const d = j.detail;
      if (typeof d === "string") message = d;
      else if (Array.isArray(d)) {
        message = d
          .map((item: unknown) => {
            if (item && typeof item === "object" && "msg" in item) {
              return String((item as { msg: string }).msg);
            }
            return JSON.stringify(item);
          })
          .join(" · ");
      } else if (d != null) message = JSON.stringify(d);
    } catch {
      /* texto plano */
    }
    throw new Error(message || `Error ${res.status}`);
  }
  if (!text) return undefined as T;
  return JSON.parse(text) as T;
}

export const api = {
  me: () => request<UserProfile>("/auth/me"),

  register: (email: string, password: string, display_name?: string) =>
    request<TokenResponse>("/auth/register", { method: "POST", json: { email, password, display_name } }),

  login: (email: string, password: string) =>
    request<TokenResponse>("/auth/login", { method: "POST", json: { email, password } }),

  google: (id_token: string) =>
    request<TokenResponse>("/auth/google", { method: "POST", json: { id_token } }),

  triage: (description: string) =>
    request<{ specialty: string; urgency: "low" | "medium" | "high"; reasoning: string }>("/triage", {
      method: "POST",
      json: { description },
    }),

  availability: (specialty: string, date: string, urgency: "low" | "medium" | "high") => {
    const q = new URLSearchParams({ specialty, date, urgency });
    return request<
      { start_at: string; end_at: string; priority_score: number; label: string | null }[]
    >(`/availability?${q.toString()}`);
  },

  predictNoShow: (specialty: string, urgency: "low" | "medium" | "high", start_at: string) =>
    request<{ no_show_risk: number; reasoning: string; features?: Record<string, unknown> }>(
      "/predict-no-show",
      { method: "POST", json: { specialty, urgency, start_at } }
    ),

  assistant: (question: string) =>
    request<{ question: string; answer: string; sources: string[]; context: string }>(
      "/assistant",
      { method: "POST", json: { question } }
    ),

  appointments: () =>
    request<
      {
        id: string;
        patient_id: string;
        patient_name: string | null;
        patient_email: string | null;
        specialty: string;
        start_at: string;
        end_at: string;
        urgency: string;
        status: string;
        description: string | null;
        triage_reasoning: string | null;
        no_show_risk: number | null;
      }[]
    >("/appointments"),

  createAppointment: (body: {
    specialty: string;
    urgency: "low" | "medium" | "high";
    start_at: string;
    description?: string | null;
    triage_reasoning?: string | null;
  }) => request<unknown>("/appointments", { method: "POST", json: body }),

  deleteAppointment: (id: string) => request<void>(`/appointments/${id}`, { method: "DELETE" }),

  riskAlerts: (threshold = 0.55) =>
    request<
      {
        appointment_id: string;
        patient_name: string | null;
        specialty: string;
        start_at: string;
        no_show_risk: number;
        suggested_action: string;
      }[]
    >(`/risk-alerts?threshold=${threshold}`),
};
