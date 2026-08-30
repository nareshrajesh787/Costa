import type { Volume } from "@/lib/types"

export function money(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value)
}

export function compactMoney(value: number) {
  if (Math.abs(value) >= 1000) {
    return `$${(value / 1000).toFixed(1)}k`
  }
  return money(value)
}

export function hours(value: number) {
  return `${value}h`
}

export function pct(value: number) {
  return `${Math.round(value * 100)}%`
}

export function severityBand(value: number) {
  if (value >= 0.72) return { label: "Severe", tone: "critical" as const }
  if (value >= 0.48) return { label: "Elevated", tone: "warn" as const }
  if (value >= 0.28) return { label: "Watch", tone: "caution" as const }
  return { label: "Low", tone: "ok" as const }
}

export function volumeLabel(volume: Volume) {
  return volume[0].toUpperCase() + volume.slice(1)
}

export function submitterLabel(value: string) {
  const map: Record<string, string> = {
    resident: "Resident",
    fisher: "Fisher",
    hotel_staff: "Hotel staff",
    lifeguard: "Lifeguard",
    municipal_scout: "Municipal scout",
  }
  return map[value] ?? value
}

export function matsLabel(value: number) {
  if (value >= 0.72) return { label: "Heavy mats", tone: "critical" as const }
  if (value >= 0.48) return { label: "A lot of seaweed", tone: "warn" as const }
  if (value >= 0.2) return { label: "Some seaweed", tone: "caution" as const }
  if (value > 0) return { label: "Light", tone: "ok" as const }
  return { label: "No report yet", tone: "ok" as const }
}

export function kindLabel(kind: string) {
  const map: Record<string, string> = {
    tourism: "Tourism",
    fisheries: "Fisheries",
    community: "Community",
    recreation: "Recreation",
    logistics: "Navigation",
  }
  return map[kind] ?? kind
}

export function relativeTime(iso: string) {
  const then = new Date(iso).getTime()
  if (Number.isNaN(then)) return iso
  const delta = Date.now() - then
  const minutes = Math.round(delta / 60000)
  if (minutes < 1) return "just now"
  if (minutes < 60) return `${minutes}m ago`
  const hoursAgo = Math.round(minutes / 60)
  if (hoursAgo < 24) return `${hoursAgo}h ago`
  return new Date(iso).toLocaleString()
}

export function localFallbackExplanation(names: {
  cleanup: string[]
  scouts: string[]
  unfunded: string[]
  budget: number
  protectedValue: number
}) {
  return {
    summary: `With ${names.budget} hours, send trucks to ${names.cleanup.join(", ") || "nowhere yet"}. Send a scout to ${names.scouts.join(", ") || "no beaches"}. This plan saves about ${new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(names.protectedValue)}.`,
    cleanupRationale: names.cleanup.length
      ? names.cleanup.map((n) => `${n} is on the truck list because it is part of the mix that saves the most money with the hours we have.`)
      : ["No beach fits in today’s hours."],
    scoutingRationale: names.scouts.map(
      (n) => `${n} is on the look-first list because we have barely checked it.`,
    ),
    tradeoffs: names.unfunded.length
      ? [`${names.unfunded[0]} does not get a crew — those hours already do more good elsewhere.`]
      : ["Every beach currently fits the shift."],
    caveat:
      "The computer already picked the beaches. This text only restates that plan. Hours and dollars are town estimates.",
    source: "local-fallback",
  }
}
