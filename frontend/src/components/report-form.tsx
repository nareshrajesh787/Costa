import { Send } from "lucide-react"
import { useState, type ReactNode } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { volumeLabel } from "@/lib/format"
import type { Submitter, Volume, Zone } from "@/lib/types"

const VOLUMES: Volume[] = ["small", "medium", "large"]
const SUBMITTERS: Submitter[] = [
  "resident",
  "fisher",
  "hotel_staff",
  "lifeguard",
  "municipal_scout",
]

export function ReportForm({
  zones,
  pending,
  onSubmit,
}: {
  zones: Zone[]
  pending: boolean
  onSubmit: (payload: {
    zoneId: string
    volume: Volume
    submitterType: Submitter
    note: string
  }) => Promise<void>
}) {
  const [zoneId, setZoneId] = useState(zones[0]?.id ?? "tourist-beach")
  const [volume, setVolume] = useState<Volume>("medium")
  const [submitterType, setSubmitterType] = useState<Submitter>("resident")
  const [note, setNote] = useState("")

  return (
    <Card>
      <CardHeader>
        <CardTitle>I saw seaweed</CardTitle>
        <CardDescription>
          Tell us which beach and how much. That updates how bad we think it is. It does not send trucks by itself.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form
          className="space-y-4"
          onSubmit={async (event) => {
            event.preventDefault()
            await onSubmit({ zoneId, volume, submitterType, note })
            setNote("")
          }}
        >
          <Field label="Which beach?">
            <Select value={zoneId} onValueChange={setZoneId}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {zones.map((zone) => (
                  <SelectItem key={zone.id} value={zone.id}>
                    {zone.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>

          <Field label="How much seaweed?">
            <div className="grid grid-cols-3 gap-2">
              {VOLUMES.map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => setVolume(item)}
                  className={`rounded-lg border px-3 py-2 text-sm font-medium ${
                    volume === item ? "border-primary bg-primary/10" : "border-border bg-background/50"
                  }`}
                >
                  {volumeLabel(item)}
                </button>
              ))}
            </div>
          </Field>

          <Field label="Who are you?">
            <Select value={submitterType} onValueChange={(v) => setSubmitterType(v as Submitter)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SUBMITTERS.map((item) => (
                  <SelectItem key={item} value={item}>
                    {item.replaceAll("_", " ")}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>

          <Field label="Optional note">
            <Textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              maxLength={280}
              placeholder="Where is it accumulating? Is access blocked?"
            />
          </Field>

          <Button type="submit" className="w-full" disabled={pending}>
            <Send className="size-4" />
            {pending ? "Sending…" : "Submit report"}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      {children}
    </div>
  )
}
