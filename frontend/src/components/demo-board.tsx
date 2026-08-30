import { Button } from "@/components/ui/button"

export function DemoBar({
  pending,
  hours,
  onSeed,
  onHours,
}: {
  pending: boolean
  hours: number
  onSeed: () => void
  onHours: (value: number) => void
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button size="sm" disabled={pending} onClick={onSeed}>
        Load today’s sample reports
      </Button>
      <div className="ml-auto flex items-center gap-2 text-sm">
        <span className="text-muted-foreground">Hours we have</span>
        <Button
          size="sm"
          variant="outline"
          disabled={pending || hours <= 4}
          onClick={() => onHours(hours - 1)}
        >
          −
        </Button>
        <span className="font-display text-lg tabular">{hours}</span>
        <Button
          size="sm"
          variant="outline"
          disabled={pending || hours >= 16}
          onClick={() => onHours(hours + 1)}
        >
          +
        </Button>
      </div>
    </div>
  )
}
