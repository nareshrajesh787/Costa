import type { ChangeEvent, Horizon, Zone } from "@/lib/types"
import { money, pct } from "@/lib/format"

export function cleanupWhyShort(zone: Zone) {
  return `Saves ${money(zone.cleanupValue)} in ${zone.requiredCrewHours} hours — best mix we can afford.`
}

export function scoutWhyShort(zone: Zone) {
  return zone.inspectionCount === 0 ? "Nobody has checked here yet." : `Only checked ${zone.inspectionCount}×. A look could change the truck list.`
}

export function boomWhyShort(zone: Zone) {
  return `${pct(zone.forecastRisk.h12)} chance it hits in 12 hours. Boom/net — not trucks.`
}

export function cleanupWhy(zone: Zone, onList: boolean) {
  if (onList) {
    return `Trucks go here because cleaning it saves about ${money(zone.cleanupValue)} in ${zone.requiredCrewHours} hours. That mix is the best total we can afford this shift — not “the worst beach first.”`
  }
  return `No trucks here this shift. It would take ${zone.requiredCrewHours} hours that already do more good on other beaches.`
}

export function scoutWhy(zone: Zone) {
  if (zone.inspectionCount === 0) {
    return `Nobody has checked ${zone.name} yet. Send a scout so we are not guessing.`
  }
  return `Only checked ${zone.inspectionCount} time${zone.inspectionCount === 1 ? "" : "s"}. A look here could change who gets trucks.`
}

export function boomWhy(zone: Zone) {
  return `${zone.name} may get hit in the next 12 hours (${pct(zone.forecastRisk.h12)} drift guess). That is a boom/net watch — not a truck order.`
}

export function seaweedWords(zone: Zone) {
  if (zone.meanSeverity >= 0.72) return "Heavy seaweed"
  if (zone.meanSeverity >= 0.48) return "A lot of seaweed"
  if (zone.meanSeverity >= 0.28) return "Some seaweed"
  if (zone.meanSeverity > 0) return "Light seaweed"
  return "No report yet"
}

export function assignmentBanner(changes: ChangeEvent[]) {
  const added = changes.filter((c) => c.kind === "cleanup_added").map((c) => c.name)
  const removed = changes.filter((c) => c.kind === "cleanup_removed").map((c) => c.name)
  if (added.length && removed.length) {
    return `${added.join(", ")} just replaced ${removed.join(", ")}. Same hours. Better total.`
  }
  if (added.length) return `${added.join(", ")} just got added to the truck list.`
  if (removed.length) return `${removed.join(", ")} just came off the truck list.`
  return null
}

export const DEMO_BLURBS: Record<string, string> = {
  "cove-surge":
    "A resident just reported a thick mat at Residential Cove. Watch the truck list — another beach may get dropped so Cove can get a crew.",
  "inlet-scout":
    "A scout checked Quiet Inlet. It should fall on the look-first list because we know more now.",
  "harbor-forecast":
    "The drift guess now says Harbor Entrance may get hit soon. That is boom-watch, not a truck order.",
}

export function horizonLabel(horizon: Horizon) {
  return horizon === "h12" ? "12 hours" : horizon === "h48" ? "48 hours" : "24 hours"
}

export function cleanupFormulaCopy(zone: Zone) {
  return [
    "We try every mix of beaches that fits in today’s hours, then keep the mix that saves the most money.",
    `${zone.name}: ${money(zone.cleanupValue)} saved · ${zone.requiredCrewHours} hours · ${money(zone.impactPerCrewHour)} per hour.`,
  ]
}

export function scoutFormulaCopy(zone: Zone) {
  return [
    "Look score = known seaweed + extra points if almost nobody has checked this beach.",
    `${zone.name} has ${zone.inspectionCount} check${zone.inspectionCount === 1 ? "" : "s"}. Extra unknown points: +${zone.uncertaintyBonus.toFixed(2)}. This does not send trucks.`,
  ]
}
