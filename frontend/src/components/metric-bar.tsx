import { compactMoney, money } from "@/lib/format"
import type { Metrics } from "@/lib/types"

export function MetricBar({ metrics }: { metrics: Metrics }) {
  const items = [
    { label: "Hour budget", value: `${metrics.crewBudget}h` },
    { label: "Assigned", value: `${metrics.assignedHours}h` },
    { label: "Remaining", value: `${metrics.remainingHours}h` },
    { label: "Value protected", value: `${compactMoney(metrics.valueProtected)}/h` },
    { label: "Unfunded risk", value: `${compactMoney(metrics.unresolvedExposure)}/h` },
  ]

  return (
    <section className="shrink-0 border-b border-border bg-card">
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5">
        {items.map((item) => (
          <div key={item.label} className="border-border px-3 py-3 sm:px-4 lg:border-r lg:last:border-r-0">
            <p className="text-[10px] font-semibold tracking-wide text-muted-foreground uppercase">{item.label}</p>
            <p className="mt-1 font-display text-lg tabular leading-none sm:text-xl">{item.value}</p>
          </div>
        ))}
      </div>
      <p className="border-t border-border px-4 py-2 text-[11px] text-muted-foreground">
        Value protected and unfunded risk are hourly exposure rates. Operating cost is{" "}
        {money(metrics.operatingCost)} for the whole shift — different units, not subtractable. Seaweed
        amounts come from filed reports, not satellite counts.
      </p>
    </section>
  )
}
