import { LogOut, Radio } from "lucide-react"
import { useEffect, useState } from "react"
import { ThemeToggle } from "@/components/theme-toggle"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import type { User } from "@/lib/auth"
import { cn } from "@/lib/utils"

export function Mark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 36 36" className={className} aria-hidden>
      <circle cx="18" cy="18" r="16" fill="none" stroke="currentColor" strokeWidth="1.4" opacity="0.35" />
      <circle cx="18" cy="18" r="11" fill="none" stroke="currentColor" strokeWidth="1.4" opacity="0.55" />
      <path
        d="M8 22c4-1 6-6 10-7 4-1 7 2 10 1"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <path
        d="M10 26c5 0 7-5 12-5 3 0 5 2 8 1"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        opacity="0.7"
      />
      <circle cx="18" cy="18" r="2.2" fill="currentColor" />
    </svg>
  )
}

export function AppHeader({
  role,
  onRole,
  online,
  grok,
  municipality,
  user,
  onLogout,
}: {
  role: "operations" | "citizen"
  onRole: (role: "operations" | "citizen") => void
  online: boolean
  grok?: boolean
  municipality?: string
  user?: User | null
  onLogout?: () => void
}) {
  const [clock, setClock] = useState("")

  useEffect(() => {
    const tick = () =>
      setClock(
        new Date().toLocaleString("en-US", {
          hour: "2-digit",
          minute: "2-digit",
          weekday: "short",
          timeZoneName: "short",
        }),
      )
    tick()
    const id = setInterval(tick, 30000)
    return () => clearInterval(id)
  }, [])

  return (
    <header className="sticky top-0 z-40 border-b border-border/80 bg-background/75 backdrop-blur-xl">
      <div className="mx-auto flex max-w-[1600px] items-center gap-4 px-4 py-3 md:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
            <Mark className="size-7" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <p className="font-display text-xl leading-none tracking-tight">Sargassum Watch</p>
              <Badge variant="ok">Live desk</Badge>
            </div>
            <p className="mt-1 truncate text-xs text-muted-foreground">
              {municipality || "Town"} · trucks vs. look first
            </p>
          </div>
        </div>

        <div className="ml-auto flex items-center gap-2 md:gap-3">
          <div
            className={cn(
              "hidden items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide sm:flex",
              online ? "border-ok/30 text-ok" : "border-critical/30 text-critical",
            )}
          >
            <Radio className="size-3.5" />
            {online ? "Live" : "Offline"}
          </div>
            {grok === false ? (
              <div className="hidden items-center gap-1.5 rounded-full border border-caution/30 px-2.5 py-1 text-[11px] font-semibold tracking-wide text-caution uppercase sm:flex">
                Grok offline
              </div>
            ) : (
              <div className="hidden items-center gap-1.5 rounded-full border border-ok/30 px-2.5 py-1 text-[11px] font-semibold tracking-wide text-ok uppercase sm:flex">
                Grok
              </div>
            )}
          <p className="hidden font-mono text-xs text-muted-foreground lg:block">{clock}</p>
          {user?.role === "operations" ? (
          <Tabs value={role} onValueChange={(v) => onRole(v as "operations" | "citizen")}>
            <TabsList>
              <TabsTrigger value="operations">Operations</TabsTrigger>
              <TabsTrigger value="citizen">Citizen</TabsTrigger>
            </TabsList>
          </Tabs>
          ) : null}
          {user ? (
            <span className="hidden max-w-[10rem] truncate text-xs text-muted-foreground md:inline">{user.name}</span>
          ) : null}
          {onLogout ? (
            <Button variant="outline" size="icon" aria-label="Sign out" onClick={onLogout}>
              <LogOut />
            </Button>
          ) : null}
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
