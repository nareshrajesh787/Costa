import { useState, type FormEvent, type ReactNode } from "react"
import { Link, useNavigate } from "react-router-dom"
import { toast } from "sonner"
import { Mark } from "@/components/app-header"
import { ThemeToggle } from "@/components/theme-toggle"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { api } from "@/lib/api"
import { cn } from "@/lib/utils"

const fieldClass =
  "h-12 rounded-md border border-border bg-muted px-3.5 text-[15px] text-foreground shadow-none placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring/30 dark:border-[#eadfcd]/30 dark:bg-[#3f372e]"

export function LoginPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [pending, setPending] = useState(false)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setPending(true)
    try {
      await api.login({ email, password })
      toast.success("Welcome back")
      navigate("/app")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not sign in")
    } finally {
      setPending(false)
    }
  }

  return (
    <AuthFrame title="Sign in" subtitle="Open today’s list for your town." compact>
      <form className="space-y-5" onSubmit={onSubmit}>
        <Field label="Email">
          <Input
            className={fieldClass}
            type="email"
            name="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </Field>
        <Field label="Password">
          <Input
            className={fieldClass}
            type="password"
            name="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </Field>
        <Button type="submit" className="h-12 w-full rounded-md text-[15px]" disabled={pending}>
          {pending ? "Signing in…" : "Sign in"}
        </Button>
        <Button
          type="button"
          variant="outline"
          className="h-11 w-full rounded-md text-[14px]"
          disabled={pending}
          onClick={async () => {
            setEmail("ops@fajardo.test")
            setPassword("password1")
            setPending(true)
            try {
              await api.login({ email: "ops@fajardo.test", password: "password1" })
              toast.success("Signed in as Fajardo ops")
              navigate("/app")
            } catch (error) {
              toast.error(error instanceof Error ? error.message : "Could not sign in")
            } finally {
              setPending(false)
            }
          }}
        >
          Sign in as Fajardo ops
        </Button>
        <p className="rounded-md border border-border bg-muted/40 px-3 py-2 text-xs text-muted-foreground">
          Judge login: <span className="font-mono text-foreground">ops@fajardo.test</span> /{" "}
          <span className="font-mono text-foreground">password1</span>
        </p>
        <p className="text-center text-sm text-muted-foreground">
          New here?{" "}
          <Link className="font-medium text-foreground underline underline-offset-4" to="/register">
            Create an account
          </Link>
        </p>
      </form>
    </AuthFrame>
  )
}

export function RegisterPage() {
  const navigate = useNavigate()
  const [pending, setPending] = useState(false)
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    municipality: "",
    region: "Puerto Rico",
    role: "operations" as "citizen" | "operations",
    lat: "18.3256",
    lng: "-65.6524",
  })

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setPending(true)
    try {
      await api.register({
        name: form.name,
        email: form.email,
        password: form.password,
        municipality: form.municipality,
        region: form.region,
        role: form.role,
        lat: Number(form.lat),
        lng: Number(form.lng),
      })
      toast.success("You’re in")
      navigate("/app")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not create account")
    } finally {
      setPending(false)
    }
  }

  function set<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  return (
    <AuthFrame
      title="Create an account"
      subtitle="Pick a town name. Neighbors type that same name when they sign up."
    >
      <form className="space-y-5" onSubmit={onSubmit}>
        <div className="grid gap-2 sm:grid-cols-2">
          <RolePick
            selected={form.role === "operations"}
            title="I send the crews"
            body="Town staff"
            onClick={() => set("role", "operations")}
          />
          <RolePick
            selected={form.role === "citizen"}
            title="I report what I see"
            body="On the beach"
            onClick={() => set("role", "citizen")}
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Your name">
            <Input
              className={fieldClass}
              name="name"
              autoComplete="name"
              required
              value={form.name}
              onChange={(e) => set("name", e.target.value)}
            />
          </Field>
          <Field label="Town name">
            <Input
              className={fieldClass}
              required
              placeholder="Fajardo"
              value={form.municipality}
              onChange={(e) => set("municipality", e.target.value)}
            />
          </Field>
        </div>

        <Field label="Email">
          <Input
            className={fieldClass}
            type="email"
            name="email"
            autoComplete="email"
            required
            value={form.email}
            onChange={(e) => set("email", e.target.value)}
          />
        </Field>
        <Field label="Password">
          <Input
            className={fieldClass}
            type="password"
            name="password"
            autoComplete="new-password"
            required
            minLength={8}
            value={form.password}
            onChange={(e) => set("password", e.target.value)}
          />
        </Field>

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Region">
            <Input
              className={fieldClass}
              placeholder="Puerto Rico"
              value={form.region}
              onChange={(e) => set("region", e.target.value)}
            />
          </Field>
          <details className="self-end">
            <summary className="mb-2 cursor-pointer text-sm text-muted-foreground">
              Change map pin from Fajardo
            </summary>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Lat">
                <Input
                  className={fieldClass}
                  inputMode="decimal"
                  value={form.lat}
                  onChange={(e) => set("lat", e.target.value)}
                />
              </Field>
              <Field label="Lng">
                <Input
                  className={fieldClass}
                  inputMode="decimal"
                  value={form.lng}
                  onChange={(e) => set("lng", e.target.value)}
                />
              </Field>
            </div>
          </details>
        </div>

        <Button type="submit" className="h-12 w-full rounded-md text-[15px]" disabled={pending}>
          {pending ? "Creating…" : "Create account"}
        </Button>
        <p className="text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link className="font-medium text-foreground underline underline-offset-4" to="/login">
            Sign in
          </Link>
        </p>
      </form>
    </AuthFrame>
  )
}

function AuthFrame({
  title,
  subtitle,
  compact,
  children,
}: {
  title: string
  subtitle: string
  compact?: boolean
  children: ReactNode
}) {
  return (
    <div className="grid min-h-screen bg-background lg:grid-cols-2">
      <div className="relative hidden flex-col justify-between bg-[#3a332b] px-10 py-10 text-[#f8f3e8] lg:flex">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5">
            <Mark className="size-8" />
            <span className="font-display text-2xl tracking-tight">Sargassum Watch</span>
          </Link>
          <ThemeToggle className="border-[#f8f3e8]/20 bg-transparent text-[#f8f3e8] hover:bg-[#f8f3e8]/10 hover:text-[#f8f3e8]" />
        </div>
        <div>
          <p className="text-sm text-[#e08a4a]">Seaweed that piles up on Caribbean beaches</p>
          <p className="mt-4 max-w-[12ch] font-display text-5xl leading-[0.95] tracking-tight">
            Too much seaweed. Not enough trucks.
          </p>
          <p className="mt-5 max-w-sm text-[15px] leading-relaxed text-[#f8f3e8]/70">
            People report what they see. Town staff get two lists: send the trucks, and go look first.
          </p>
          <div className="mt-10 grid max-w-sm gap-3">
            <div className="border border-[#f8f3e8]/15 bg-[#2a241c] px-4 py-4">
              <p className="text-[11px] text-[#e08a4a]">Send the trucks</p>
              <p className="mt-1.5 font-display text-xl leading-tight">Hotel beach · Harbor · Cove</p>
            </div>
            <div className="border border-[#f8f3e8]/15 px-4 py-4">
              <p className="text-[11px] text-[#f8f3e8]/50">Go look first</p>
              <p className="mt-1.5 font-display text-xl leading-tight text-[#f8f3e8]/80">Quiet Inlet</p>
            </div>
          </div>
        </div>
        <Link to="/" className="text-sm text-[#f8f3e8]/55 hover:text-[#f8f3e8]">
          ← Back to home
        </Link>
      </div>

      <div className="flex min-h-screen flex-col bg-background dark:bg-[#221c16]">
        <div className="flex items-center justify-between px-5 py-4">
          <Link to="/" className="flex items-center gap-2 text-foreground lg:invisible">
            <Mark className="size-7" />
            <span className="font-display text-xl">Sargassum Watch</span>
          </Link>
          <div className="flex items-center gap-3">
            <Link to="/" className="text-sm text-muted-foreground hover:text-foreground">
              Home
            </Link>
            <ThemeToggle className="lg:hidden" />
          </div>
        </div>
        <div className={cn("flex flex-1 justify-center px-5 py-10", compact && "items-center py-6")}>
          <div className="w-full max-w-[420px]">
            <h1 className="font-display text-4xl tracking-tight text-foreground">{title}</h1>
            <p className="mt-2 mb-8 text-[15px] leading-relaxed text-muted-foreground">{subtitle}</p>
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}

function RolePick({
  selected,
  title,
  body,
  onClick,
}: {
  selected: boolean
  title: string
  body: string
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "border px-4 py-3.5 text-left transition-colors",
        selected
          ? "border-primary bg-primary text-primary-foreground"
          : "border-border bg-card text-foreground",
      )}
    >
      <p className="font-display text-lg leading-tight">{title}</p>
      <p className={cn("mt-1 text-xs", selected ? "text-primary-foreground/70" : "text-muted-foreground")}>{body}</p>
    </button>
  )
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="space-y-1.5">
      <Label className="text-[13px]">{label}</Label>
      {children}
    </div>
  )
}
