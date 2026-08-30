import { compactMoney, money } from "@/lib/format"
import type { Metrics } from "@/lib/types"

export function MetricBar({ metrics }: { metrics: Metrics }) {
  const items = [
    { label: "Hour budget", value: `${metrics.crewBudget}h` },
    { label: "Assigned", value: `${metrics.assignedHours}h` },
    { label: "Remaining", value: `${metrics.remainingHours}h` },
    { label: "Value protected", value: compactMoney(metrics.valueProtected) },
    { label: "Unfunded risk", value: compactMoney(metrics.unresolvedExposure) },
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
        Operating cost {money(metrics.operatingCost)}. Simulated planning data — not satellite counts.
      </p>
    </section>
  )
}
