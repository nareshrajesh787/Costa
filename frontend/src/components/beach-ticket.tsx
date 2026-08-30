import { Badge } from "@/components/ui/badge"
import { matsLabel } from "@/lib/format"
import type { Zone } from "@/lib/types"
import { cn } from "@/lib/utils"

export function BeachTicket({
  zone,
  rank,
  mode,
  changed,
  onOpen,
}: {
  zone: Zone
  rank?: number
  mode: "cleanup" | "scout" | "wait"
  changed?: boolean
  onOpen: (id: string) => void
}) {
  const mats = matsLabel(zone.meanSeverity)
  const reason =
    mode === "cleanup"
      ? `Needs ${zone.requiredCrewHours} hours. ${zone.blurb}`
      : mode === "scout"
        ? zone.inspectionCount === 0
          ? "Nobody has checked this beach yet."
          : `Last checked ${zone.inspectionCount} time${zone.inspectionCount === 1 ? "" : "s"}.`
        : `Needs ${zone.requiredCrewHours} hours — not enough crew left today.`

  return (
    <button
      type="button"
      onClick={() => onOpen(zone.id)}
      className={cn(
        "flex w-full items-start gap-4 rounded-xl border border-border bg-card px-4 py-4 text-left transition-colors hover:bg-muted/40",
        changed && "pulse-ring ring-1 ring-accent",
      )}
    >
      {rank ? (
        <span className="font-display text-2xl leading-none text-muted-foreground/80">{rank}</span>
      ) : null}
      <span className="min-w-0 flex-1">
        <span className="flex flex-wrap items-center gap-2">
          <span className="font-display text-xl leading-none">{zone.name}</span>
          <Badge variant={mats.tone}>{mats.label}</Badge>
        </span>
        <span className="mt-1.5 block text-sm leading-relaxed text-muted-foreground">{reason}</span>
      </span>
    </button>
  )
}
