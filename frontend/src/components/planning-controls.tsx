import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import type { Horizon } from "@/lib/types"

export function PlanningControls({
  budget,
  horizon,
  explorationC,
  forecastWeight,
  pending,
  onBudget,
  onHorizon,
  onExploration,
  onForecastWeight,
}: {
  budget: number
  horizon: Horizon
  explorationC: number
  forecastWeight: number
  pending: boolean
  onBudget: (value: number) => void
  onHorizon: (value: Horizon) => void
  onExploration: (value: number) => void
  onForecastWeight: (value: number) => void
}) {
  const [open, setOpen] = useState(false)
  const [localBudget, setLocalBudget] = useState(budget)
  const [localC, setLocalC] = useState(explorationC)
  const [localW, setLocalW] = useState(forecastWeight)

  useEffect(() => setLocalBudget(budget), [budget])
  useEffect(() => setLocalC(explorationC), [explorationC])
  useEffect(() => setLocalW(forecastWeight), [forecastWeight])

  return (
    <Card>
      <CardHeader>
        <CardTitle>Hours and look-ahead</CardTitle>
        <CardDescription>More hours can put another beach on the truck list. The look-first list is separate.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <div className="mb-2 flex items-center justify-between text-sm">
            <Label>Crew-hour budget</Label>
            <span className="font-mono tabular">{localBudget}h</span>
          </div>
          <Slider
            min={4}
            max={16}
            step={1}
            value={[localBudget]}
            disabled={pending}
            onValueChange={([value]) => setLocalBudget(value)}
            onValueCommit={([value]) => onBudget(value)}
          />
        </div>
        <div>
          <Label className="mb-2 block">Drift scenario horizon</Label>
          <Tabs value={horizon} onValueChange={(v) => onHorizon(v as Horizon)}>
            <TabsList className="w-full">
              <TabsTrigger value="h12" className="flex-1" disabled={pending}>
                12h
              </TabsTrigger>
              <TabsTrigger value="h24" className="flex-1" disabled={pending}>
                24h
              </TabsTrigger>
              <TabsTrigger value="h48" className="flex-1" disabled={pending}>
                48h
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
        <button
          type="button"
          className="text-xs font-medium text-muted-foreground underline"
          onClick={() => setOpen((v) => !v)}
        >
          {open ? "Hide advanced weights" : "Show advanced weights"}
        </button>
        {open ? (
          <div className="space-y-4">
            <div>
              <div className="mb-2 flex justify-between text-sm">
                <Label>Exploration c</Label>
                <span className="font-mono">{localC.toFixed(2)}</span>
              </div>
              <Slider
                min={0.2}
                max={1.4}
                step={0.04}
                value={[localC]}
                disabled={pending}
                onValueChange={([value]) => setLocalC(value)}
                onValueCommit={([value]) => onExploration(value)}
              />
            </div>
            <div>
              <div className="mb-2 flex justify-between text-sm">
                <Label>Forecast weight</Label>
                <span className="font-mono">{localW.toFixed(2)}</span>
              </div>
              <Slider
                min={0}
                max={0.8}
                step={0.05}
                value={[localW]}
                disabled={pending}
                onValueChange={([value]) => setLocalW(value)}
                onValueCommit={([value]) => onForecastWeight(value)}
              />
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}
