import type { ReactNode } from "react"
import { LayoutDashboard, LogOut, MapPin, RotateCcw, Waves } from "lucide-react"
import { Mark } from "@/components/app-header"
import { Button } from "@/components/ui/button"
import type { User } from "@/lib/auth"
import type { DemoEvent } from "@/lib/types"
import { cn } from "@/lib/utils"

export function AppSidebar({
  view,
  onView,
  canToggleView,
  pending,
  user,
  demoEvents,
  disclaimer,
  onLogout,
  onSeed,
  onReset,
  onPlay,
  className,
}: {
  view: "operations" | "citizen"
  onView: (view: "operations" | "citizen") => void
  canToggleView: boolean
  municipality?: string
  pending: boolean
  user?: User | null
  demoEvents: DemoEvent[]
  disclaimer?: string
  onLogout?: () => void
  onSeed: () => void
  onReset: () => void
  onPlay: (id: string) => void
  className?: string
}) {
  return (
    <aside className={cn("flex h-full w-[min(100%,16rem)] shrink-0 flex-col border-r border-border bg-card", className)}>
      <div className="flex items-center gap-2.5 px-5 py-5">
        <div className="flex size-9 items-center justify-center rounded-xl bg-primary text-primary-foreground">
          <Mark className="size-5" />
        </div>
        <p className="font-display text-lg leading-none">Sargassum Watch</p>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-3">
        {canToggleView ? (
          <>
            <NavItem
              icon={<LayoutDashboard />}
              label="Operations"
              active={view === "operations"}
              onClick={() => onView("operations")}
            />
            <NavItem
              icon={<MapPin />}
              label="Citizen report"
              active={view === "citizen"}
              onClick={() => onView("citizen")}
            />
          </>
        ) : (
          <NavItem icon={<MapPin />} label="Citizen report" active />
        )}

        <p className="px-3 pt-5 pb-1 text-[11px] font-semibold tracking-wide text-muted-foreground uppercase">
          Demo
        </p>
        <NavItem icon={<Waves />} label="Seed 8-hour shift" disabled={pending} onClick={onSeed} />
        <NavItem icon={<RotateCcw />} label="Reset demo" disabled={pending} onClick={onReset} />
        {demoEvents.map((event) => (
          <NavItem
            key={event.id}
            label={event.title}
            disabled={pending}
            onClick={() => onPlay(event.id)}
          />
        ))}
      </nav>

      <div className="px-3 pb-3">
        <div className="rounded-2xl bg-muted/70 px-4 py-4">
          <p className="text-sm font-medium">Simulated planning data</p>
          <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
            {disclaimer || "Hours and dollars are town estimates. Seaweed amounts come from reports, not satellites."}
          </p>
        </div>
        <div className="mt-3 flex items-center justify-between px-1">
          <p className="truncate text-xs text-muted-foreground">{user?.name}</p>
          {onLogout ? (
            <Button variant="ghost" size="icon" className="size-8" aria-label="Sign out" onClick={onLogout}>
              <LogOut />
            </Button>
          ) : null}
        </div>
      </div>
    </aside>
  )
}

function NavItem({
  icon,
  label,
  active,
  disabled,
  onClick,
}: {
  icon?: ReactNode
  label: string
  active?: boolean
  disabled?: boolean
  onClick?: () => void
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={cn(
        "flex w-full items-center gap-3 rounded-xl px-3 py-2 text-left text-sm transition-colors disabled:opacity-50",
        active ? "bg-muted font-medium text-foreground" : "text-muted-foreground hover:bg-muted/60 hover:text-foreground",
      )}
    >
      {icon ? <span className="[&_svg]:size-4">{icon}</span> : <span className="w-4" />}
      {label}
    </button>
  )
}
