import { useEffect, useState, type FormEvent } from "react"
import { ArrowRight, Loader2 } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { Slider } from "@/components/ui/slider"
import { money } from "@/lib/format"
import type { AskAnswer, Explanation, Metrics } from "@/lib/types"

export function BudgetCard({
  metrics,
  pending,
  onBudget,
}: {
  metrics: Metrics
  pending: boolean
  onBudget: (hours: number) => void
}) {
  const [hours, setHours] = useState(metrics.crewBudget)
  useEffect(() => setHours(metrics.crewBudget), [metrics.crewBudget])
  const used = metrics.crewBudget ? (metrics.assignedHours / metrics.crewBudget) * 100 : 0

  return (
    <div className="rounded-xl border border-border bg-card p-4 sm:p-5">
      <p className="text-sm text-muted-foreground">Crew-hour budget</p>
      <p className="mt-1 font-display text-3xl tabular">{metrics.remainingHours}h left</p>
      <p className="mt-1 text-sm text-muted-foreground">
        {metrics.assignedHours} assigned of {metrics.crewBudget} · operating cost {money(metrics.operatingCost)}
      </p>
      <div className="mt-4">
        <div className="mb-2 flex items-center justify-between text-sm">
          <Label>Hours this shift</Label>
          <span className="font-mono tabular">{hours}h</span>
        </div>
        <Slider
          min={4}
          max={16}
          step={1}
          value={[hours]}
          disabled={pending}
          onValueChange={([value]) => setHours(value)}
          onValueCommit={([value]) => onBudget(value)}
        />
      </div>
      <div className="mt-4">
        <div className="mb-1 flex justify-between text-xs text-muted-foreground">
          <span>Hours used</span>
          <span>{Math.round(used)}%</span>
        </div>
        <Progress value={Math.min(100, Math.max(0, used))} />
      </div>
    </div>
  )
}

export function ExplainPanel({
  explanation,
  ask,
  loading,
  asking,
  onExplain,
  onAsk,
}: {
  explanation: Explanation | null
  ask: AskAnswer | null
  loading: boolean
  asking: boolean
  onExplain: () => void
  onAsk: (question: string) => void
}) {
  const [question, setQuestion] = useState("")

  function submitAsk(event: FormEvent) {
    event.preventDefault()
    const next = question.trim()
    if (!next) return
    onAsk(next)
  }

  return (
    <div className="rounded-xl border border-border bg-card p-4 sm:p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm font-medium">Grok explains the lists. It does not pick them.</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Structured JSON only — summary, why trucks, why scouts, tradeoffs, caveat.
          </p>
        </div>
        <Button onClick={onExplain} disabled={loading} className="shrink-0">
          {loading ? <Loader2 className="animate-spin" /> : null}
          Explain this dispatch
          <ArrowRight />
        </Button>
      </div>

      {explanation ? (
        <div className="mt-4 space-y-3 text-sm leading-relaxed">
          <Badge variant={explanation.source === "grok" || explanation.source?.includes("xAI") ? "ok" : "caution"}>
            {explanation.source === "local-fallback" ? "Local fallback" : explanation.model || explanation.source}
          </Badge>
          <p>{explanation.summary}</p>
          {explanation.cleanupRationale?.length ? (
            <List title="Why these trucks" items={explanation.cleanupRationale} />
          ) : null}
          {explanation.scoutingRationale?.length ? (
            <List title="Why these scouts" items={explanation.scoutingRationale} />
          ) : null}
          {explanation.tradeoffs?.length ? <List title="Tradeoffs" items={explanation.tradeoffs} /> : null}
          {explanation.caveat ? <p className="text-xs text-muted-foreground">{explanation.caveat}</p> : null}
        </div>
      ) : (
        <p className="mt-4 text-sm text-muted-foreground">
          Rankings already come from EMA + knapsack + UCB-inspired scores. This button only restates those numbers.
        </p>
      )}

      <form onSubmit={submitAsk} className="mt-4 flex flex-col gap-2 sm:flex-row">
        <Input
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask why a beach was skipped…"
          maxLength={280}
        />
        <Button type="submit" variant="outline" disabled={asking || !question.trim()} className="shrink-0">
          {asking ? <Loader2 className="animate-spin" /> : null}
          Ask
        </Button>
      </form>
      {ask ? (
        <div className="mt-3 space-y-1 text-sm">
          <p>{ask.answer}</p>
          <p className="text-xs text-muted-foreground">
            {ask.caveat} · {ask.source}
          </p>
        </div>
      ) : null}
    </div>
  )
}

function List({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">{title}</p>
      <ul className="mt-1 list-disc space-y-1 pl-4">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  )
}
