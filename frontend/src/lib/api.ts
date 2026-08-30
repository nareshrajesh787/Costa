import { authHeaders, clearToken, setToken, type User } from "@/lib/auth"
import type { AskAnswer, DashboardState, Explanation, Health, Horizon, Volume } from "@/lib/types"

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init)
  if (response.status === 401) {
    clearToken()
    if (!path.includes("/auth/")) {
      window.location.href = "/login"
    }
  }
  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try {
      const body = await response.json()
      message = body.detail || message
      if (Array.isArray(body.detail)) {
        message = body.detail.map((d: { msg?: string }) => d.msg).join(" ")
      }
    } catch {
      const detail = await response.text().catch(() => "")
      if (detail) message = detail
    }
    throw new Error(message)
  }
  return (await response.json()) as T
}

export const api = {
  health: () => request<Health>("/api/health"),
  register: (body: {
    name: string
    email: string
    password: string
    municipality: string
    region: string
    role: "citizen" | "operations"
    lat: number
    lng: number
  }) =>
    request<{ token: string; user: User }>("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then((data) => {
      setToken(data.token)
      return data
    }),
  login: (body: { email: string; password: string }) =>
    request<{ token: string; user: User }>("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then((data) => {
      setToken(data.token)
      return data
    }),
  me: () => request<User>("/api/me", { headers: authHeaders() }),
  state: () => request<DashboardState>("/api/state", { headers: authHeaders() }),
  report: (body: {
    zoneId: string
    volume: Volume
    submitterType: string
    note: string
  }) =>
    request<DashboardState>("/api/reports", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(body),
    }),
  inspect: (body: { zoneId: string; observedVolume: Volume; note: string }) =>
    request<DashboardState>("/api/inspect", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(body),
    }),
  settings: (body: {
    crewBudget?: number
    explorationC?: number
    forecastWeight?: number
    horizon?: Horizon
    lat?: number
    lng?: number
    region?: string
  }) =>
    request<DashboardState>("/api/settings", {
      method: "PATCH",
      headers: authHeaders(),
      body: JSON.stringify(body),
    }),
  seed: () =>
    request<DashboardState>("/api/demo/seed", {
      method: "POST",
      headers: authHeaders(),
    }),
  reset: () =>
    request<DashboardState>("/api/demo/reset", {
      method: "POST",
      headers: authHeaders(),
    }),
  play: (eventId: string) =>
    request<DashboardState>("/api/demo/play", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ eventId }),
    }),
  briefing: async () => {
    const response = await fetch("/api/briefing", { headers: authHeaders() })
    if (!response.ok) throw new Error("Could not copy briefing")
    return response.text()
  },
  explain: (state: DashboardState) =>
    request<Explanation>("/api/explain", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ summaryContext: state }),
    }),
  ask: (question: string, state: DashboardState) =>
    request<AskAnswer>("/api/ask", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ question, summaryContext: state }),
    }),
}
