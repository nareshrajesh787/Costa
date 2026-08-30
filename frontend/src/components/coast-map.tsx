import type { Horizon, Zone } from "@/lib/types"
import { matsLabel, pct } from "@/lib/format"
import { cn } from "@/lib/utils"

export function CoastMap({
  zones,
  cleanupIds,
  scoutIds,
  containmentIds,
  horizon,
  selectedId,
  onSelect,
}: {
  zones: Zone[]
  cleanupIds: string[]
  scoutIds: string[]
  containmentIds: string[]
  horizon: Horizon
  selectedId: string | null
  onSelect: (id: string) => void
}) {
  const hours = horizon === "h12" ? "12h" : horizon === "h48" ? "48h" : "24h"
  const ordered = [...zones].sort((a, b) => a.position.y - b.position.y || a.position.x - b.position.x)

  return (
    <div className="p-4">
      <div className="mb-2 flex items-center justify-between text-[10px] tracking-wide text-muted-foreground uppercase">
        <span>North → south</span>
        <span>{hours} drift scenario</span>
      </div>
      <div className="overflow-hidden rounded-xl border border-border">
        {ordered.map((zone) => {
          const trucks = cleanupIds.includes(zone.id)
          const look = scoutIds.includes(zone.id)
          const boom = containmentIds.includes(zone.id)
          const band = matsLabel(zone.meanSeverity)
          const drift = zone.forecastRisk[horizon]
          const role = trucks ? "Cleanup now" : look ? "Scout next" : boom ? "Boom watch" : "Unassigned"
          return (
            <button
              key={zone.id}
              type="button"
              onClick={() => onSelect(zone.id)}
              className={cn(
                "grid w-full grid-cols-[minmax(0,1fr)_4.5rem] border-b border-border text-left last:border-b-0",
                selectedId === zone.id && "bg-muted/80",
                trucks && "bg-accent/10",
              )}
            >
              <span className="flex min-w-0 items-center justify-between gap-2 px-3 py-2.5">
                <span className="min-w-0">
                  <span className="block truncate text-sm font-medium">{zone.name}</span>
                  <span className="text-[11px] text-muted-foreground">{role}</span>
                </span>
                <span
                  className={cn(
                    "shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold",
                    band.tone === "critical" && "bg-critical/15 text-critical",
                    band.tone === "warn" && "bg-warn/15 text-warn",
                    band.tone === "caution" && "bg-caution/15 text-caution",
                    band.tone === "ok" && "bg-ok/15 text-ok",
                  )}
                >
                  {pct(zone.meanSeverity)}
                </span>
              </span>
              <span className="flex items-center justify-center border-l border-border bg-[#8eaea4]/35 text-[11px] tabular dark:bg-[#1a2826]">
                {pct(drift)}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}

export function MapLegend({ count }: { count: number }) {
  return (
    <p className="text-xs text-muted-foreground">
      {count} zone{count === 1 ? "" : "s"} from live state. Right column is a drift scenario, not a satellite.
    </p>
  )
}
