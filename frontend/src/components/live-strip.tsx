import { CloudSun, Waves, Wind } from "lucide-react"
import type { DashboardState } from "@/lib/types"

export function LiveStrip({ weather }: { weather: NonNullable<DashboardState["weather"]> }) {
  const nws = weather.nws
  const tide = weather.tide
  return (
    <section className="border-b border-border/80 bg-card/70">
      <div className="mx-auto grid max-w-5xl gap-4 px-5 py-5 md:grid-cols-3">
        <Stat
          icon={CloudSun}
          kicker={nws?.source || "National Weather Service"}
          title={nws?.short || weather.summary || "Coastal weather"}
          body={
            nws
              ? [nws.tempF != null ? `${nws.tempF}°F` : null, nws.wind || null, nws.nextShort ? `Later: ${nws.nextShort}` : null]
                  .filter(Boolean)
                  .join(" · ")
              : weather.temperatureF != null
                ? `${weather.temperatureF}°F · ${weather.summary}`
                : weather.summary || ""
          }
        />
        <Stat
          icon={Wind}
          kicker="Open-Meteo · live wind & sea"
          title={`${Math.round(weather.windSpeedMph ?? weather.windSpeedMs * 2.2)} mph ${weather.windCompass || ""}`.trim()}
          body={`Waves ${weather.waveHeightFt ?? (weather.waveHeightM * 3.3).toFixed(1)} ft · current ${weather.currentCompass || ""} ${weather.currentSpeedMs.toFixed(1)} m/s`}
        />
        <Stat
          icon={Waves}
          kicker={tide ? `NOAA tide · ${tide.stationName}` : "NOAA tide"}
          title={tide?.next ? tide.next.kind : "Tide gauge"}
          body={
            tide?.next
              ? `${tide.next.when?.slice(11, 16) || ""} · ${tide.next.heightFt} ft  (${Math.round(tide.distanceKm)} km away)`
              : "Gauge did not answer just now"
          }
        />
      </div>
    </section>
  )
}

function Stat({
  icon: Icon,
  kicker,
  title,
  body,
}: {
  icon: typeof CloudSun
  kicker: string
  title: string
  body: string
}) {
  return (
    <div>
      <p className="flex items-center gap-1.5 text-[11px] font-semibold tracking-wide text-accent uppercase">
        <Icon className="size-3.5" />
        {kicker}
      </p>
      <p className="mt-1 font-display text-2xl leading-tight">{title}</p>
      <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{body}</p>
    </div>
  )
}
