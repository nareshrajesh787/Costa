import { Play, RotateCcw, WandSparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import type { DemoEvent } from "@/lib/types"
import { cn } from "@/lib/utils"

export function DemoDock({
  events,
  played,
  pending,
  onReset,
  onPlay,
  onBriefing,
}: {
  events: DemoEvent[]
  played: string[]
  pending: boolean
  onReset: () => void
  onPlay: (id: string) => void
  onBriefing: () => void
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Live demo controls</CardTitle>
        <CardDescription>
          Budget starts at 8 crew-hours. Event 1 is the tradeoff judges should see. Keys 1–3 play events; R resets.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" onClick={onReset} disabled={pending}>
            <RotateCcw /> Reset demo
          </Button>
          <Button variant="accent" size="sm" onClick={onBriefing} disabled={pending}>
            <Play /> Run live briefing
          </Button>
        </div>
        {events.map((event, index) => {
          const done = played.includes(event.id)
          return (
            <button
              key={event.id}
              type="button"
              disabled={pending}
              onClick={() => onPlay(event.id)}
              className={cn(
                "w-full rounded-lg border px-3 py-2.5 text-left transition-colors hover:bg-muted/60",
                done ? "border-primary/40 bg-primary/8" : "border-border",
              )}
            >
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-semibold">
                  {index + 1}. {event.title}
                </p>
                <WandSparkles className="size-3.5 text-accent" />
              </div>
              <p className="mt-1 text-xs text-muted-foreground">{event.narration}</p>
            </button>
          )
        })}
      </CardContent>
    </Card>
  )
}
