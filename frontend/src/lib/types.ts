export type Volume = "small" | "medium" | "large"
export type Submitter =
  | "resident"
  | "fisher"
  | "hotel_staff"
  | "lifeguard"
  | "municipal_scout"
export type Horizon = "h12" | "h24" | "h48"

export interface ForecastRisk {
  h12: number
  h24: number
  h48: number
}

export interface ZoneBreakdown {
  severity: number
  economicWeight: number
  hourlyRevenueAtRisk: number
  immediateExposure: number
  forecastWeight: number
  forecastHorizon: Horizon
  forecastRisk: number
  forecastComponent: number
  cleanupValue: number
  requiredCrewHours: number
  impactPerCrewHour: number
  operatingCost: number
  exploitScore: number
  uncertaintyBonus: number
  scoutPriority: number
  inspectionCount: number
  totalInspections: number
  explorationC: number
}

export interface Zone {
  id: string
  name: string
  shortName: string
  kind: string
  blurb: string
  accessNotes: string
  economicWeight: number
  hourlyRevenueAtRisk: number
  cleanupCostPerHour: number
  requiredCrewHours: number
  meanSeverity: number
  inspectionCount: number
  position: { x: number; y: number }
  currentVector: { speed: number; direction: number }
  forecastRisk: ForecastRisk
  reports: Report[]
  immediateExposure: number
  cleanupValue: number
  forecastComponent: number
  scoutPriority: number
  exploitScore: number
  uncertaintyBonus: number
  impactPerCrewHour: number
  operatingCost: number
  forecastHorizonRisk: number
  projected: {
    h12: { x: number; y: number }
    h24: { x: number; y: number }
    h48: { x: number; y: number }
  }
  forecastSource?: "live" | "scenario"
  breakdown: ZoneBreakdown
  assignedCleanup?: boolean
  cleanupRank?: number
  scoutRank?: number
  assigned?: boolean
  role?: string
  reason?: string
}

export interface Report {
  id: string
  zoneId: string
  volume: Volume
  submitterType: Submitter
  note: string
  timestamp: string
  source: string
}

export interface Metrics {
  crewBudget: number
  assignedHours: number
  remainingHours: number
  valueProtected: number
  unresolvedExposure: number
  unfundedHours: number
  operatingCost: number
  totalImmediateExposure: number
  totalInspections: number
  zoneCount: number
  selectedCount: number
  // valueProtected / unresolvedExposure are hourly exposure rates; operatingCost is
  // a whole-shift total. They are deliberately not subtractable.
  units?: Record<string, string>
}

export interface ChangeEvent {
  zoneId: string
  name: string
  kind: "cleanup_added" | "cleanup_removed" | "scout_shift"
}

export interface DemoEvent {
  id: string
  title: string
  narration: string
  kind: string
  payload: Record<string, unknown>
}

export interface DashboardState {
  community: {
    name: string
    region: string
    shift: string
    disclaimer: string
    lat?: number
    lng?: number
  }
  weather?: {
    source: string
    fetchedAt: string
    summary?: string
    temperatureF?: number | null
    humidity?: number | null
    windSpeedMs: number
    windSpeedMph?: number
    windDirection: number
    windCompass?: string
    currentSpeedMs: number
    currentDirection: number
    currentCompass?: string
    waveHeightM: number
    waveHeightFt?: number
    nws?: {
      source: string
      name: string
      short: string
      detailed: string
      tempF?: number
      wind: string
      nextName?: string
      nextShort?: string
    } | null
    tide?: {
      source: string
      stationId: string
      stationName: string
      distanceKm: number
      next?: { when: string; heightFt: number; kind: string } | null
    } | null
    sources?: Array<{ name: string; usedFor: string }>
  }
  user?: {
    id: number
    name: string
    email: string
    role: "citizen" | "operations"
  } | null
  ai?: { provider: string; endpoint: string }
  settings: {
    crewBudget: number
    explorationC: number
    forecastWeight: number
    horizon: Horizon
  }
  generatedAt: string
  highlight: boolean
  changes: ChangeEvent[]
  zones: Zone[]
  cleanupNow: Zone[]
  unfunded: Zone[]
  scoutNext: Zone[]
  scoutRanked: Zone[]
  containment: Zone[]
  metrics: Metrics
  selection: {
    ids: string[]
    method: string
    horizon: Horizon
    forecastWeight: number
    explorationC: number
  }
  formulas: Record<string, string>
  reports: Report[]
  eventLog: Array<{
    id: string
    kind: string
    title: string
    detail: string
    timestamp: string
    zoneId?: string
  }>
  demoEvents: DemoEvent[]
  playedEvents: string[]
  lastDemoEvent?: DemoEvent
}

export interface Explanation {
  summary: string
  cleanupRationale: string[]
  scoutingRationale: string[]
  tradeoffs: string[]
  caveat: string
  source: string
  reason?: string
  model?: string
}

export interface AskAnswer {
  answer: string
  caveat: string
  source: string
}

export interface AiTier {
  tier: "grok" | "ollama" | "local-fallback"
  provider: string
  model: string | null
  cascade: string
  role: string
}

export interface Health {
  ok: boolean
  grok?: { ok: boolean; provider: string; model: string; configured: boolean }
  ai?: { ok: boolean; provider: string; model: string; configured: boolean }
  ollama?: { ok: boolean; models: string[] }
}
