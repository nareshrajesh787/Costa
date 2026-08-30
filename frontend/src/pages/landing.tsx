import { Link } from "react-router-dom"
import { Mark } from "@/components/app-header"
import { ThemeToggle } from "@/components/theme-toggle"
import { Button } from "@/components/ui/button"

export function LandingPage() {
  return (
    <div className="min-h-screen">
      <SiteHeader />

      <section className="px-5 pt-16 pb-16 text-center md:pt-20 md:pb-20">
        <p className="text-sm text-accent">Sargassum is seaweed that washes onto Caribbean beaches in huge piles.</p>
        <h1 className="mx-auto mt-4 max-w-[16ch] font-display text-[2.75rem] leading-[0.98] tracking-[-0.03em] sm:text-6xl md:text-7xl">
          Too much seaweed. Not enough trucks.
        </h1>
        <p className="mx-auto mt-6 max-w-[46ch] text-base leading-relaxed text-muted-foreground">
          Neighbors report what they see. The app picks which beaches get a cleanup crew today — and
          which ones just need someone to go look. The AI writes a short explanation. It does not
          choose the plan.
        </p>
        <div className="mt-8 flex justify-center">
          <Button size="lg" className="rounded-md px-6" asChild>
            <Link to="/register">Create an account</Link>
          </Button>
        </div>
        <HeroApp />
      </section>

      <section id="problem" className="scroll-mt-24 border-y border-border/60">
        <div className="mx-auto grid max-w-5xl gap-10 px-5 py-16 text-center sm:grid-cols-3">
          <Stat n="$120M" src="EPA, 2018" d="What Caribbean towns spent in one year hauling this seaweed off beaches" />
          <Stat n="$25k" src="U.S. Virgin Islands" d="What one dense event can cost per day" />
          <Stat n="Tourism" src="NOAA" d="What residents worry about most, right next to the cleanup bill" />
        </div>
      </section>

      <section className="mx-auto max-w-3xl px-5 py-20 text-center">
        <h2 className="font-display text-4xl tracking-tight md:text-5xl">Everyone reports. Nobody can clean it all.</h2>
        <p className="mt-6 text-base leading-relaxed text-muted-foreground">
          On a bad day the seaweed hits the hotel beach, the fishing dock, and the neighborhood path
          at the same time. A town only has a few crew-hours. Group chats fill up. Nobody has a
          clear “do this first” list.
        </p>
        <p className="mt-4 text-base leading-relaxed text-muted-foreground">
          Sargassum Watch is that list. People on the sand file a report. Town staff get two
          answers: where to send the trucks, and where to send someone just to check. Then they can
          see why.
        </p>
        <p className="mt-4 text-sm text-muted-foreground">
          The dollar figures above are from EPA and NOAA. They describe the region. They are not
          made-up losses for a fake town. Your town types in its own beach values.
        </p>
      </section>

      <section id="product" className="scroll-mt-24 border-y border-border/60">
        <div className="mx-auto max-w-5xl px-5 py-20">
          <div className="mx-auto max-w-xl text-center">
            <h2 className="font-display text-4xl tracking-tight md:text-5xl">Two jobs. One screen.</h2>
            <p className="mt-4 text-muted-foreground">People on the beach file. Town staff decide where the hours go.</p>
          </div>
          <div className="mt-12 grid gap-3 md:grid-cols-2">
            <Role
              kicker="If you live or work on the coast"
              title="See seaweed. Report it."
              points={[
                "Choose the beach, how big the pile looks, and who you are.",
                "Add a note if a path is blocked or it smells bad.",
                "That report is saved. The picture of that beach updates right away.",
              ]}
            />
            <Role
              kicker="If you run the cleanup"
              title="Spend the hours you actually have."
              points={[
                "Cleanup: the app picks the best set of beaches that fit today’s crew time.",
                "Go look: a second list for beaches nobody has checked recently.",
                "Weather comes from a live marine forecast. It is a hint, not a crystal ball.",
              ]}
            />
          </div>
        </div>
      </section>

      <section id="how" className="scroll-mt-24 mx-auto max-w-5xl px-5 py-20 text-center">
        <h2 className="font-display text-4xl tracking-tight md:text-5xl">How a day works</h2>
        <p className="mx-auto mt-4 max-w-md text-muted-foreground">
          One report is enough to change the plan. Every new report runs the same steps again.
        </p>
        <div className="mt-14 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Step n="01" title="Start a town" body="Create an account with your town’s name. Neighbors join that same name. Map pin defaults to Fajardo, Puerto Rico — you can move it." />
          <Step n="02" title="People report" body="Someone on the beach says small, medium, or large. New reports update the picture. One loud report does not wipe everything else." />
          <Step n="03" title="Check the weather" body="Live wind and current data show which beaches the seaweed might be pushing toward." />
          <Step n="04" title="Send the crews" body="The app rebuilds today’s list. Staff can open the numbers, then ask the AI to say the plan out loud." />
        </div>
      </section>

      <section className="border-y border-border/60">
        <div className="mx-auto max-w-5xl px-5 py-20 text-center">
          <h2 className="font-display text-4xl tracking-tight md:text-5xl">The moment that makes the demo click</h2>
          <p className="mx-auto mt-4 max-w-lg text-muted-foreground">
            Give the town 8 hours of crew time. If every beach gets a truck, there is nothing to
            talk about. The story is who loses a slot when a worse pile is reported.
          </p>
          <div className="mt-12 grid gap-3 text-left md:grid-cols-2">
            <Ticket
              kicker="Before"
              title="Hotel beach, harbor, fishing dock"
              meta="Quiet Inlet only gets a look — almost nobody has been there. The neighborhood cove is waiting."
            />
            <Ticket
              kicker="Someone reports a big pile at the cove"
              title="Hotel beach, harbor, neighborhood cove"
              meta="The fishing dock loses its slot. Quiet Inlet still only gets a look. “We haven’t checked” is not the same as “send the trucks.”"
            />
          </div>
          <p className="mx-auto mt-8 max-w-lg text-sm leading-relaxed text-muted-foreground">
            The hotel beach stays because lots of money and people depend on it. The cove takes the
            dock’s three hours because that is the better use of the day — not because we added a
            fourth truck. Quiet Inlet stays on the look list on purpose.
          </p>
        </div>
      </section>

      <section id="engine" className="scroll-mt-24 mx-auto max-w-5xl px-5 py-20 text-center">
        <h2 className="font-display text-4xl tracking-tight md:text-5xl">The computer picks. The AI only talks.</h2>
        <p className="mx-auto mt-4 max-w-lg text-muted-foreground">
          Same reports always produce the same plan. That is on purpose. The AI is a briefing, not
          a boss. If it is offline, the plan still appears, with a backup explanation.
        </p>
        <div className="mt-12 grid gap-3 text-left sm:grid-cols-2">
          <Ticket
            kicker="Send cleanup"
            title="The beaches that fit today’s hours"
            meta="It looks at how bad each beach is, how much that beach matters, and how many hours it takes. Then it picks the mix that protects the most — without going over the clock."
          />
          <Ticket
            kicker="Go look"
            title="The beaches we know least about"
            meta="A beach that nobody has checked gets a boost. That does not mean send a truck. It means send a person with eyes."
          />
        </div>
        <div className="mt-3 grid gap-3 text-left sm:grid-cols-2 lg:grid-cols-4">
          <Metric label="How bad is it?" value="Running average" note="New reports pull the picture toward what people just saw." />
          <Metric label="What is at stake?" value="Beach × dollars" note="A hotel beach and a quiet lagoon are not worth the same." />
          <Metric label="Who should look?" value="Least-checked first" note="Blind spots are useful. They are not automatic cleanups." />
          <Metric label="Who gets the trucks?" value="Best mix in budget" note="Shown as hours and value. Not “whoever shouted last.”" />
        </div>
      </section>

      <section className="border-y border-border/60">
        <div className="mx-auto max-w-5xl px-5 py-20 text-center">
          <h2 className="font-display text-4xl tracking-tight md:text-5xl">What you see on the screen</h2>
          <p className="mx-auto mt-4 max-w-md text-muted-foreground">
            Every number is either a real report, live weather, or a value the town typed in.
          </p>
          <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            <Stat n="8h" src="Today’s hours" d="How much crew time you have. Change it and the list rebuilds." />
            <Stat n="Saved" src="Value protected" d="What you keep by cleaning the beaches that made the cut — using your own numbers." />
            <Stat n="Waiting" src="Didn’t fit" d="Beaches that still matter but would steal hours from a better mix." />
            <Stat n="AI note" src="Explanation" d="A short write-up of the plan that is already on screen. It cannot reshuffle the list." />
          </div>
        </div>
      </section>

      <section id="data" className="scroll-mt-24 mx-auto max-w-5xl px-5 py-20 text-center">
        <h2 className="font-display text-4xl tracking-tight md:text-5xl">What is real. What is yours. What we are not claiming.</h2>
        <p className="mx-auto mt-4 max-w-md text-muted-foreground">
          A judge should be able to point at any number and know where it came from.
        </p>
        <div className="mt-12 grid gap-3 text-left sm:grid-cols-2">
          <Ticket kicker="Real, live" title="Reports from people" meta="Saved for your town. They drive how bad each beach looks." />
          <Ticket kicker="Real, live" title="Wind and current" meta="From Open-Meteo at your map pin. A hint about where seaweed may drift. Not a trained “bloom predictor.”" />
          <Ticket kicker="You type this in" title="Hours and beach values" meta="How many crew hours you have, and how much each beach matters. Those are your estimates." />
          <Ticket kicker="Not in this app" title="Satellites and bloom forecasts" meta="Nice later. Not needed to start. We do not pretend we already built them." />
        </div>
      </section>

      <section id="claims" className="scroll-mt-24 grid lg:grid-cols-2">
        <div className="bg-[#3a332b] px-8 py-16 text-[#f8f3e8] md:px-14">
          <p className="text-sm text-[#f8f3e8]/55">Fair to say</p>
          <ul className="mt-6 space-y-5">
            <Claim title="We flag beaches nobody has checked">So someone can go look. That list is separate from the cleanup trucks.</Claim>
            <Claim title="We pick the best mix that fits the hours">With a small number of beaches, the computer can try the combinations and keep the best one.</Claim>
            <Claim title="Weather is a live overlay">Wind and current from a public forecast. A sketch of where piles might move. Not a trained AI weather model.</Claim>
            <Claim title="The AI only explains">It reads the plan the computer already made. If it is down, a backup paragraph still covers the same plan.</Claim>
          </ul>
        </div>
        <div className="bg-card px-8 py-16 md:px-14">
          <p className="text-sm text-muted-foreground">Not fair to say</p>
          <ul className="mt-6 space-y-5">
            <Claim muted title="We predict seaweed with machine learning">We do not. No satellite feed. No trained bloom model.</Claim>
            <Claim muted title="The AI sends the trucks">It does not. Cleanup and “go look” are computed first. Words come after.</Claim>
            <Claim muted title="This is a full mapping product">It is a simple coast sketch so you can see the beaches. Not GIS software.</Claim>
            <Claim muted title="These dollars are a real town’s losses">EPA and NOAA numbers are regional. Your beach values are estimates you enter.</Claim>
          </ul>
        </div>
      </section>

      <section className="mx-auto max-w-3xl px-5 py-20">
        <h2 className="text-center font-display text-4xl tracking-tight md:text-5xl">If you only have a minute</h2>
        <div className="mt-12 space-y-8">
          <Faq
            q="Does the AI decide where crews go?"
            a="No. The app computes the lists first. The AI only turns those lists into a short briefing."
          />
          <Faq
            q="Do we need satellites to use this?"
            a="No. You start with people on the beach and live weather. Satellites would be a later add-on."
          />
          <Faq
            q="What if the AI is down during a demo?"
            a="The plan still shows. A backup paragraph explains the same numbers."
          />
          <Faq
            q="Can two towns use this?"
            a="Yes. Each town name is its own workspace. Neighbors join by typing that name when they sign up."
          />
          <Faq
            q="Are the dollar amounts real for our town?"
            a="No. EPA and NOAA figures explain why this problem is expensive in the Caribbean. Your beach values are numbers your team types in."
          />
        </div>
      </section>

      <section className="border-t border-border/60 px-5 py-20 text-center">
        <h2 className="mx-auto max-w-[18ch] font-display text-4xl tracking-tight md:text-5xl">
          Set up your town this afternoon.
        </h2>
        <p className="mx-auto mt-4 max-w-md text-muted-foreground">
          Create an account, share the town name with people on the beach, and take the first
          report. That is enough to change the list.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Button size="lg" className="rounded-md px-6" asChild>
            <Link to="/register">Create an account</Link>
          </Button>
          <Button size="lg" variant="outline" className="rounded-md px-6" asChild>
            <Link to="/login">Sign in</Link>
          </Button>
        </div>
      </section>

      <footer className="border-t border-border/60">
        <div className="mx-auto flex max-w-5xl flex-col gap-2 px-5 py-8 text-center text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between sm:text-left">
          <span className="font-display text-foreground">Sargassum Watch</span>
          <p>People report · the app ranks · the AI explains</p>
        </div>
      </footer>
    </div>
  )
}

function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-border/50 bg-[#f6f1e6]/90 backdrop-blur-md dark:bg-[#1c1814]/90">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-3">
        <Link to="/" className="flex items-center gap-2.5 text-foreground">
          <Mark className="size-7" />
          <span className="font-display text-[1.35rem] leading-none tracking-tight">Sargassum Watch</span>
        </Link>
        <nav className="hidden items-center gap-6 text-sm text-muted-foreground md:flex">
          <a href="#problem" className="hover:text-foreground">
            Problem
          </a>
          <a href="#product" className="hover:text-foreground">
            How it works
          </a>
          <a href="#engine" className="hover:text-foreground">
            The plan
          </a>
          <a href="#claims" className="hover:text-foreground">
            Honest bit
          </a>
        </nav>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Button variant="ghost" asChild>
            <Link to="/login">Sign in</Link>
          </Button>
          <Button className="rounded-md" asChild>
            <Link to="/register">Create account</Link>
          </Button>
        </div>
      </div>
    </header>
  )
}

function Stat({ n, src, d }: { n: string; src: string; d: string }) {
  return (
    <div>
      <p className="font-display text-5xl tracking-tight">{n}</p>
      <p className="mt-2 text-xs text-accent">{src}</p>
      <p className="mt-2 text-sm text-muted-foreground">{d}</p>
    </div>
  )
}

function Step({ n, title, body }: { n: string; title: string; body: string }) {
  return (
    <div className="border border-border bg-card px-6 py-8 text-left">
      <p className="font-mono text-xs text-muted-foreground">{n}</p>
      <h3 className="mt-3 font-display text-3xl">{title}</h3>
      <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{body}</p>
    </div>
  )
}

function Ticket({ kicker, title, meta }: { kicker: string; title: string; meta: string }) {
  return (
    <div className="border border-border bg-card px-6 py-6">
      <p className="text-xs text-accent">{kicker}</p>
      <p className="mt-2 font-display text-2xl leading-tight">{title}</p>
      <p className="mt-2 text-sm text-muted-foreground">{meta}</p>
    </div>
  )
}

function Role({ kicker, title, points }: { kicker: string; title: string; points: string[] }) {
  return (
    <div className="border border-border bg-card px-6 py-8">
      <p className="text-xs text-accent">{kicker}</p>
      <h3 className="mt-2 font-display text-3xl">{title}</h3>
      <ul className="mt-5 space-y-3 text-sm leading-relaxed text-muted-foreground">
        {points.map((point) => (
          <li key={point}>{point}</li>
        ))}
      </ul>
    </div>
  )
}

function Metric({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <div className="border border-border bg-card px-5 py-5">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-2 font-display text-xl leading-tight">{value}</p>
      <p className="mt-2 text-xs leading-relaxed text-muted-foreground">{note}</p>
    </div>
  )
}

function Claim({ title, children, muted }: { title: string; children: string; muted?: boolean }) {
  return (
    <li>
      <p className={`font-display text-2xl leading-snug ${muted ? "text-muted-foreground" : ""}`}>{title}</p>
      <p className={`mt-1.5 text-sm leading-relaxed ${muted ? "text-muted-foreground" : "text-[#f8f3e8]/65"}`}>
        {children}
      </p>
    </li>
  )
}

function Faq({ q, a }: { q: string; a: string }) {
  return (
    <div className="border-b border-border/70 pb-8">
      <h3 className="font-display text-2xl">{q}</h3>
      <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{a}</p>
    </div>
  )
}

function HeroApp() {
  return (
    <div className="mx-auto mt-14 w-full max-w-4xl overflow-hidden border border-border bg-card text-left">
      <div className="flex items-center justify-between gap-4 bg-[#3a332b] px-5 py-3 text-[#f8f3e8]">
        <p className="font-display text-lg">Fajardo · today</p>
        <p className="font-mono text-xs opacity-80">8 hours of crew time</p>
      </div>
      <div className="relative">
        <svg viewBox="0 0 800 220" className="h-36 w-full sm:h-44" aria-hidden>
          <rect width="800" height="220" className="fill-[#e8dcc8] dark:fill-[#26211b]" />
          <path
            d="M0 118 C90 88, 180 148, 280 126 C370 106, 430 68, 520 86 C620 106, 700 58, 800 76 L800 220 L0 220 Z"
            className="fill-[#f6f1e6] dark:fill-[#1c1814]"
          />
          <path
            d="M0 118 C90 88, 180 148, 280 126 C370 106, 430 68, 520 86 C620 106, 700 58, 800 76"
            fill="none"
            className="stroke-[#3a332b] dark:stroke-[#eadfcd]"
            strokeWidth="1.4"
          />
          <circle cx="268" cy="114" r="8" className="fill-[#b86a32]" />
          <circle cx="430" cy="80" r="7" className="fill-[#3a332b] dark:fill-[#eadfcd]" />
          <circle cx="610" cy="98" r="6" fill="none" className="stroke-[#8a7a62]" strokeWidth="2" />
        </svg>
        <div className="relative -mt-10 grid gap-3 px-4 pb-4 sm:grid-cols-2 sm:px-5">
          <div className="border border-border bg-card px-4 py-4">
            <p className="text-[11px] text-accent">Send the trucks</p>
            <ul className="mt-3 space-y-2.5">
              <HeroRow name="Hotel beach" detail="3 hours" />
              <HeroRow name="Harbor" detail="2 hours" />
              <HeroRow name="Neighborhood cove" detail="3 hours · just added" hot />
            </ul>
          </div>
          <div className="border border-border bg-card px-4 py-4">
            <p className="text-[11px] text-muted-foreground">Go look first</p>
            <ul className="mt-3 space-y-2.5">
              <HeroRow name="Quiet Inlet" detail="Almost nobody has checked" />
              <HeroRow name="Fishing dock" detail="Lost its slot to the cove" mute />
            </ul>
          </div>
        </div>
      </div>
      <p className="border-t border-border px-5 py-3 text-sm text-muted-foreground">
        A neighbor just reported a big pile at the cove. The dock lost three hours. The inlet still
        only gets a look.
      </p>
    </div>
  )
}

function HeroRow({
  name,
  detail,
  hot,
  mute,
}: {
  name: string
  detail: string
  hot?: boolean
  mute?: boolean
}) {
  return (
    <li className={`flex items-baseline justify-between gap-3 ${mute ? "opacity-50" : ""}`}>
      <span className="font-display text-xl leading-none">{name}</span>
      <span className={`text-xs ${hot ? "text-accent" : "text-muted-foreground"}`}>{detail}</span>
    </li>
  )
}
