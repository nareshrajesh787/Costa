import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Sheet, SheetContent } from "@/components/ui/sheet"
import { ScoreBreakdown } from "@/components/zone-card"
import { boomWhy, cleanupWhy, seaweedWords, scoutWhy } from "@/lib/copy"
import { money, pct } from "@/lib/format"
import type { Volume, Zone } from "@/lib/types"

export function ZoneDetail({
  zone,
  open,
  onList,
  onScout,
  onBoom,
  onClose,
  onInspect,
}: {
  zone: Zone | null
  open: boolean
  onList: boolean
  onScout: boolean
  onBoom: boolean
  onClose: () => void
  onInspect: (zoneId: string, volume: Volume) => void
}) {
  if (!zone) return null
  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent title={zone.name}>
        <div className="flex h-full flex-col overflow-y-auto p-6 pt-12">
          <h2 className="font-display text-3xl">{zone.name}</h2>
          <p className="mt-2 text-sm text-muted-foreground">{zone.blurb}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Badge variant={onList ? "ok" : "outline"}>{onList ? "Getting trucks" : "No trucks this shift"}</Badge>
            {onScout ? <Badge variant="caution">Look first</Badge> : null}
            {onBoom ? <Badge variant="warn">Boom watch</Badge> : null}
          </div>

          <p className="mt-5 text-sm leading-relaxed">
            {onList ? cleanupWhy(zone, true) : onScout ? scoutWhy(zone) : onBoom ? boomWhy(zone) : cleanupWhy(zone, false)}
          </p>

          <dl className="mt-5 grid grid-cols-2 gap-2 text-sm">
            <Row label="Seaweed right now" value={seaweedWords(zone)} />
            <Row label="How bad (0–100)" value={pct(zone.meanSeverity)} />
            <Row label="Hours to clean" value={`${zone.requiredCrewHours}h`} />
            <Row label="Money cleaning saves" value={money(zone.cleanupValue)} />
            <Row label="Times checked" value={String(zone.inspectionCount)} />
            <Row label="Drift guess in 24h" value={pct(zone.forecastRisk.h24)} />
          </dl>

          <div className="mt-6 rounded-xl bg-muted/60 p-4">
            <p className="mb-2 text-sm font-medium">Why this rank?</p>
            <ScoreBreakdown zone={zone} mode={onList ? "cleanup" : "scout"} />
          </div>

          <div className="mt-6">
            <p className="mb-2 text-sm font-medium">A scout just looked</p>
            <p className="mb-2 text-xs text-muted-foreground">This updates what we know. It does not send trucks by itself.</p>
            <div className="flex gap-2">
              {(["small", "medium", "large"] as Volume[]).map((volume) => (
                <Button key={volume} variant="outline" size="sm" onClick={() => onInspect(zone.id, volume)}>
                  {volume} mats
                </Button>
              ))}
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-muted/50 px-3 py-2">
      <dt className="text-[10px] tracking-wide text-muted-foreground uppercase">{label}</dt>
      <dd className="mt-0.5 font-medium">{value}</dd>
    </div>
  )
}
