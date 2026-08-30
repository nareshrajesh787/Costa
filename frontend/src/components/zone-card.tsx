import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { Badge } from "@/components/ui/badge"
import { money, pct, severityBand } from "@/lib/format"
import type { Horizon, Zone } from "@/lib/types"
import { cn } from "@/lib/utils"

export function ZoneCard({
  zone,
  mode,
  rank,
  changed,
  totalInspections,
  explorationC,
  horizon,
  onOpen,
}: {
  zone: Zone
  mode: "cleanup" | "scout" | "boom"
  rank: number
  changed?: boolean
  totalInspections: number
  explorationC: number
  horizon: Horizon
  onOpen: (id: string) => void
}) {
  const band = severityBand(zone.meanSeverity)
  const risk = zone.forecastRisk[horizon]
  return (
    <article
      className={cn(
        "reorder-in overflow-hidden rounded-xl border border-border bg-card",
        changed && "pulse-ring ring-1 ring-accent",
      )}
    >
      <button type="button" className="flex w-full items-start gap-3 px-4 pt-4 pb-2 text-left" onClick={() => onOpen(zone.id)}>
        <span className="font-mono text-xs text-muted-foreground">{rank}</span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-display text-xl leading-none">{zone.name}</h3>
            <Badge variant={band.tone}>{band.label}</Badge>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">{zone.blurb}</p>
        </div>
      </button>

      <dl className="grid grid-cols-2 gap-px bg-border sm:grid-cols-4">
        <Stat label="Severity" value={pct(zone.meanSeverity)} />
        <Stat label="At risk / hr" value={money(zone.immediateExposure)} />
        <Stat
          label={horizon === "h12" ? "12h drift" : horizon === "h48" ? "48h drift" : "24h drift"}
          value={pct(risk)}
        />
        <Stat
          label={mode === "scout" ? "Checks" : "Crew hours"}
          value={mode === "scout" ? String(zone.inspectionCount) : `${zone.requiredCrewHours}h`}
        />
      </dl>

      <div className="px-4" onClick={(event) => event.stopPropagation()}>
        <Accordion type="single" collapsible>
          <AccordionItem value="why" className="border-b-0">
            <AccordionTrigger className="py-2.5 text-xs text-muted-foreground">Why this rank?</AccordionTrigger>
            <AccordionContent>
              <ScoreBreakdown
                zone={zone}
                mode={mode}
                totalInspections={totalInspections}
                explorationC={explorationC}
              />
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </div>
    </article>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-card px-3 py-2">
      <dt className="text-[10px] tracking-wide text-muted-foreground uppercase">{label}</dt>
      <dd className="font-mono text-sm tabular">{value}</dd>
    </div>
  )
}

export function ScoreBreakdown({
  zone,
  mode,
  totalInspections = 0,
  explorationC = 0.7,
}: {
  zone: Zone
  mode: string
  totalInspections?: number
  explorationC?: number
}) {
  const b = zone.breakdown
  if (mode === "scout") {
    return (
      <div className="space-y-2 pb-1 text-sm leading-relaxed">
        <p className="rounded-lg bg-muted/70 px-3 py-2 font-mono text-[11px] leading-snug">
          Priority = (severity × economic weight) + c √(ln(T) / max(1, inspections))
        </p>
        <p className="text-muted-foreground">
          {zone.inspectionCount <= 1
            ? `${zone.name} gets an uncertainty boost because it has been inspected ${zone.inspectionCount === 0 ? "zero times" : "only once"}. This is the look-first list — not a truck order.`
            : `${zone.name} ranks here because reported severity is ${pct(b.severity)} and the economic weight is ${b.economicWeight}.`}
        </p>
        <p className="font-mono text-[11px] text-muted-foreground">
          T={totalInspections} · inspections={b.inspectionCount} · c={explorationC.toFixed(2)} · bonus=
          {b.uncertaintyBonus.toFixed(2)} · score={zone.scoutPriority.toFixed(2)}
        </p>
      </div>
    )
  }
  if (mode === "boom") {
    return (
      <p className="text-sm text-muted-foreground">
        12-hour drift guess is {pct(zone.forecastRisk.h12)}. Stage boom before landfall. This is a scenario overlay, not
        the knapsack.
      </p>
    )
  }
  return (
    <div className="space-y-2 pb-1 text-sm leading-relaxed">
      <p className="rounded-lg bg-muted/70 px-3 py-2 font-mono text-[11px] leading-snug">
        Exact 0/1 knapsack: highest total cleanup value that still fits the crew-hour budget.
      </p>
      <p className="text-muted-foreground">
        {zone.name} is in the set because {money(b.cleanupValue)} in {b.requiredCrewHours} hours (
        {money(b.impactPerCrewHour)}/hour) raises the shift total. This is not “worst beach first.”
      </p>
    </div>
  )
}
