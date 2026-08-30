import { ScrollArea } from "@/components/ui/scroll-area"
import { relativeTime, submitterLabel, volumeLabel } from "@/lib/format"
import type { DashboardState } from "@/lib/types"

export function ActivityFeed({ state }: { state: DashboardState }) {
  return (
    <div className="glass-panel rounded-xl p-4">
      <h3 className="font-display text-lg">Activity</h3>
      <p className="mb-3 text-xs text-muted-foreground">Reports, scouts, and parameter changes.</p>
      <ScrollArea className="h-56">
        <ol className="space-y-3 pr-3">
          {state.eventLog
            .filter((item, index, list) => index === 0 || item.title !== list[index - 1]?.title)
            .slice(0, 12)
            .map((item, index) => (
            <li key={`${item.id}-${item.timestamp}-${index}`} className="border-l-2 border-primary/40 pl-3">
              <p className="text-sm font-medium">{item.title}</p>
              <p className="text-xs text-muted-foreground">{item.detail}</p>
              <p className="mt-0.5 font-mono text-[10px] text-muted-foreground">{relativeTime(item.timestamp)}</p>
            </li>
          ))}
        </ol>
      </ScrollArea>
      <div className="mt-4">
        <h4 className="text-[11px] font-semibold tracking-wide text-muted-foreground uppercase">
          Recent reports
        </h4>
        <ul className="mt-2 space-y-2">
          {state.reports.slice(0, 5).map((report) => (
            <li key={report.id} className="text-xs">
              <span className="font-semibold">{volumeLabel(report.volume)}</span> · {submitterLabel(report.submitterType)} ·{" "}
              {state.zones.find((z) => z.id === report.zoneId)?.name}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
