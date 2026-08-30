import { useCallback, useEffect, useMemo, useState } from "react"
import { Navigate, useNavigate } from "react-router-dom"
import { Menu } from "lucide-react"
import { toast } from "sonner"
import { AppSidebar } from "@/components/app-sidebar"
import { CoastMap, MapLegend } from "@/components/coast-map"
import { BudgetCard, ExplainPanel } from "@/components/explain-panel"
import { MetricBar } from "@/components/metric-bar"
import { ReportForm } from "@/components/report-form"
import { ThemeToggle } from "@/components/theme-toggle"
import { ZoneCard } from "@/components/zone-card"
import { ZoneDetail } from "@/components/zone-detail"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent } from "@/components/ui/sheet"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { api } from "@/lib/api"
import { clearToken, getToken, type User } from "@/lib/auth"
import { assignmentBanner } from "@/lib/copy"
import { localFallbackExplanation } from "@/lib/format"
import type { AskAnswer, DashboardState, Explanation, Horizon } from "@/lib/types"
import { cn } from "@/lib/utils"

export function DashboardPage() {
  const navigate = useNavigate()
  const [user, setUser] = useState<User | null>(null)
  const [state, setState] = useState<DashboardState | null>(null)
  const [role, setRole] = useState<"operations" | "citizen">("operations")
  const [online, setOnline] = useState(true)
  const [pending, setPending] = useState(false)
  const [explainLoading, setExplainLoading] = useState(false)
  const [asking, setAsking] = useState(false)
  const [explanation, setExplanation] = useState<Explanation | null>(null)
  const [ask, setAsk] = useState<AskAnswer | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [changedIds, setChangedIds] = useState<string[]>([])
  const [ready, setReady] = useState(false)
  const [story, setStory] = useState<string | null>(null)
  const [menu, setMenu] = useState(false)

  const apply = useCallback((next: DashboardState, message?: string) => {
    setState(next)
    setOnline(true)
    setExplanation(null)
    setAsk(null)
    const ids = next.changes.map((c) => c.zoneId)
    setChangedIds(ids)
    if (ids.length) window.setTimeout(() => setChangedIds([]), 4000)
    const demo = next.lastDemoEvent?.narration
    const swap = assignmentBanner(next.changes)
    setStory([demo, swap].filter(Boolean).join(" "))
    if (message) toast.success(message)
  }, [])

  const run = useCallback(
    async (fn: () => Promise<DashboardState>, success?: string) => {
      setPending(true)
      try {
        const next = await fn()
        apply(next, success)
        return next
      } catch (error) {
        setOnline(false)
        toast.error(error instanceof Error ? error.message : "Request failed")
        return null
      } finally {
        setPending(false)
      }
    },
    [apply],
  )

  useEffect(() => {
    if (!getToken()) {
      setReady(true)
      return
    }
    Promise.all([api.me(), api.state()])
      .then(([me, desk]) => {
        setUser(me)
        setRole(me.role === "citizen" ? "citizen" : "operations")
        apply(desk)
      })
      .catch(() => clearToken())
      .finally(() => setReady(true))
  }, [apply])

  const selectedZone = useMemo(
    () => state?.zones.find((z) => z.id === selectedId) ?? null,
    [state, selectedId],
  )

  async function explain() {
    if (!state) return
    setExplainLoading(true)
    try {
      setExplanation(await api.explain(state))
    } catch {
      setExplanation(
        localFallbackExplanation({
          cleanup: state.cleanupNow.map((z) => z.name),
          scouts: state.scoutNext.map((z) => z.name),
          unfunded: state.unfunded.map((z) => z.name),
          budget: state.metrics.crewBudget,
          protectedValue: state.metrics.valueProtected,
        }),
      )
    } finally {
      setExplainLoading(false)
    }
  }

  async function askPlan(question: string) {
    if (!state) return
    setAsking(true)
    try {
      setAsk(await api.ask(question, state))
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Ask failed — using local note")
      setAsk({
        answer: "Could not reach Grok. Rankings still come from the engine on this page, not from a model.",
        caveat: "Local fallback. No new numbers were invented.",
        source: "local-fallback",
      })
    } finally {
      setAsking(false)
    }
  }

  if (!ready) {
    return <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">Opening…</div>
  }
  if (!getToken()) return <Navigate to="/login" replace />
  if (!state) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">
        {online ? "Loading…" : "API is down."}
      </div>
    )
  }

  const cleanupIds = state.selection.ids
  const scoutList = state.scoutNext.filter((zone) => !cleanupIds.includes(zone.id))
  const boomList = state.containment
  const boomIds = boomList.map((z) => z.id)
  const view = user?.role === "operations" ? role : "citizen"
  const horizon = state.settings.horizon
  const T = state.metrics.totalInspections
  const c = state.settings.explorationC

  const sidebar = (
    <AppSidebar
      view={view}
      onView={(next) => {
        setRole(next)
        setMenu(false)
      }}
      canToggleView={user?.role === "operations"}
      municipality={state.community.name}
      pending={pending}
      user={user}
      demoEvents={state.demoEvents}
      disclaimer={state.community.disclaimer}
      className="h-full w-full border-0 lg:h-screen lg:w-60 lg:border-r"
      onLogout={() => {
        clearToken()
        navigate("/")
      }}
      onSeed={() => {
        setMenu(false)
        void run(() => api.seed(), "Seeded 8-hour shift")
      }}
      onReset={() => {
        setMenu(false)
        setStory(null)
        void run(() => api.reset(), "Demo reset")
      }}
      onPlay={(id) => {
        setMenu(false)
        void run(() => api.play(id))
      }}
    />
  )

  return (
    <div className="flex min-h-screen bg-background">
      <div className="hidden lg:block">{sidebar}</div>
      <Sheet open={menu} onOpenChange={setMenu}>
        <SheetContent side="left" title="Menu" className="max-w-60 p-0">
          {sidebar}
        </SheetContent>
      </Sheet>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 shrink-0 items-center gap-3 border-b border-border px-3 sm:px-5">
          <Button variant="ghost" size="icon" className="lg:hidden" aria-label="Open menu" onClick={() => setMenu(true)}>
            <Menu />
          </Button>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{state.community.name}</p>
            <p className="truncate text-xs text-muted-foreground">Simulated planning data</p>
          </div>
          {user?.role === "operations" ? (
            <div className="flex items-center gap-1 rounded-lg bg-muted p-1 text-sm">
              <button
                type="button"
                className={cn("rounded-md px-2 py-1 sm:px-3", view === "operations" && "bg-background shadow-sm")}
                onClick={() => setRole("operations")}
              >
                Operations
              </button>
              <button
                type="button"
                className={cn("rounded-md px-2 py-1 sm:px-3", view === "citizen" && "bg-background shadow-sm")}
                onClick={() => setRole("citizen")}
              >
                Citizen
              </button>
            </div>
          ) : null}
          <ThemeToggle />
        </header>

        {view === "operations" ? <MetricBar metrics={state.metrics} /> : null}

        <div className="min-h-0 flex-1 overflow-auto">
          {view === "citizen" ? (
            <div className="mx-auto w-full max-w-lg p-4 sm:p-6">
              <ReportForm
                zones={state.zones}
                pending={pending}
                onSubmit={async (payload) => {
                  await run(() => api.report(payload), "Report saved — lists recalculated")
                }}
              />
            </div>
          ) : (
            <div className="space-y-5 p-3 sm:p-5">
              {story ? (
                <div className="rounded-xl border border-accent/30 bg-accent/10 px-4 py-3 text-sm">{story}</div>
              ) : null}

              <div className="grid grid-cols-1 gap-5 lg:grid-cols-[minmax(0,0.35fr)_minmax(0,0.65fr)]">
                <div className="space-y-4">
                  <div className="rounded-xl border border-border bg-card">
                    <div className="flex flex-col gap-2 px-4 pt-3 sm:flex-row sm:items-start sm:justify-between">
                      <div>
                        <p className="text-sm font-medium">Coastal grid</p>
                        <MapLegend count={state.zones.length} />
                      </div>
                      <Tabs
                        value={horizon}
                        onValueChange={(value) => void run(() => api.settings({ horizon: value as Horizon }))}
                      >
                        <TabsList>
                          <TabsTrigger value="h12" disabled={pending}>
                            12h
                          </TabsTrigger>
                          <TabsTrigger value="h24" disabled={pending}>
                            24h
                          </TabsTrigger>
                          <TabsTrigger value="h48" disabled={pending}>
                            48h
                          </TabsTrigger>
                        </TabsList>
                      </Tabs>
                    </div>
                    <CoastMap
                      zones={state.zones}
                      cleanupIds={cleanupIds}
                      scoutIds={scoutList.map((z) => z.id)}
                      containmentIds={boomIds}
                      horizon={horizon}
                      selectedId={selectedId}
                      onSelect={setSelectedId}
                    />
                  </div>
                  {boomList.length ? (
                    <div className="rounded-xl border border-border bg-card px-4 py-3">
                      <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Boom watch</p>
                      <p className="mt-1 text-sm">
                        {boomList.map((z) => z.name).join(", ")} — deploy boom before projected landfall. Forecast
                        scenario, not knapsack.
                      </p>
                    </div>
                  ) : null}
                  <BudgetCard
                    metrics={state.metrics}
                    pending={pending}
                    onBudget={(hours) => void run(() => api.settings({ crewBudget: hours }))}
                  />
                </div>

                <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
                  <section>
                    <h2 className="mb-1 font-display text-2xl">Cleanup now</h2>
                    <p className="mb-3 text-xs text-muted-foreground">
                      Exact 0/1 knapsack — highest-value set that fits the hour budget.
                    </p>
                    <div className="space-y-3">
                      {state.cleanupNow.length ? (
                        state.cleanupNow.map((zone, index) => (
                          <ZoneCard
                            key={zone.id}
                            zone={zone}
                            mode="cleanup"
                            rank={index + 1}
                            changed={changedIds.includes(zone.id)}
                            totalInspections={T}
                            explorationC={c}
                            horizon={horizon}
                            onOpen={setSelectedId}
                          />
                        ))
                      ) : (
                        <p className="text-sm text-muted-foreground">
                          No trucks assigned. Seed a shift, file a report, or raise the hour budget.
                        </p>
                      )}
                    </div>
                  </section>
                  <section>
                    <h2 className="mb-1 font-display text-2xl">Scout next</h2>
                    <p className="mb-3 text-xs text-muted-foreground">
                      UCB-inspired uncertainty score. Separate from cleanup.
                    </p>
                    <div className="space-y-3">
                      {scoutList.length ? (
                        scoutList.map((zone, index) => (
                          <ZoneCard
                            key={zone.id}
                            zone={zone}
                            mode="scout"
                            rank={index + 1}
                            changed={changedIds.includes(zone.id)}
                            totalInspections={T}
                            explorationC={c}
                            horizon={horizon}
                            onOpen={setSelectedId}
                          />
                        ))
                      ) : (
                        <p className="text-sm text-muted-foreground">No scout targets yet.</p>
                      )}
                    </div>
                  </section>
                </div>
              </div>

              <ExplainPanel
                explanation={explanation}
                ask={ask}
                loading={explainLoading}
                asking={asking}
                onExplain={() => void explain()}
                onAsk={(question) => void askPlan(question)}
              />
            </div>
          )}
        </div>
      </div>

      <ZoneDetail
        zone={selectedZone}
        open={Boolean(selectedZone)}
        onList={Boolean(selectedZone && cleanupIds.includes(selectedZone.id))}
        onScout={Boolean(selectedZone && scoutList.some((z) => z.id === selectedZone.id))}
        onBoom={Boolean(selectedZone && boomIds.includes(selectedZone.id))}
        onClose={() => setSelectedId(null)}
        onInspect={(zoneId, observedVolume) => {
          void run(() => api.inspect({ zoneId, observedVolume, note: "Scout look." }), "Logged a look")
        }}
      />
    </div>
  )
}
