# Run-of-show — 3:30 target

Rehearse against a clock. Every step below is a keystroke, not a hunt through menus.

## Before you start recording

1. Backend up: `cd backend && .venv/bin/uvicorn app.main:app --port 8000`
2. Frontend up: `cd frontend && npm run dev`
3. Browser at `http://localhost:5173`, **already signed in as `ops@fajardo.test`** (login screen has
   a one-click button). Do not register on stage.
4. Press **`R`** once so you open on a clean desk.
5. Close the sidebar-heavy narrow window — share at 1366px or wider.

Keys: **`S`** seed · **`1`/`2`/`3`** play events · **`R`** reset.

---

## 0:00 – 0:25 · The problem

> "Sargassum is seaweed that piles onto Caribbean beaches by the ton. On a bad day it hits the hotel
> beach, the fishing dock, and a neighborhood path at the same time — and the town has eight
> crew-hours. Not eight per beach. Eight. Somebody has to choose, and right now that choice happens
> in a group chat."

On screen: the empty desk. Point at the first-run banner — no reports yet, so the desk says so
plainly instead of inventing a list.

## 0:25 – 0:50 · What is actually live

Point at the header and the sidebar card.

> "Two things are real here. Reports filed by people on the sand, and live marine conditions —
> Open-Meteo wind and currents, the National Weather Service forecast, and NOAA tides from the
> nearest real gauge to this town's coordinates. The dollar weights are the town's own estimates and
> we label them that way everywhere."

## 0:50 – 1:20 · Seed the shift — press `S`

> "Three reports come in: the hotel beach, the harbor, the dock. The engine scores every zone and
> solves an exact knapsack over the eight hours — the provably best set that fits, not a greedy
> guess."

Point at: Cleanup now (3 zones, 8/8 hours used), Scout next as a *separate* list, and the per-zone
`Why this rank?` disclosure.

## 1:20 – 2:00 · The money shot — press `1`

> "A neighbor reports a big pile at the residential cove."

Wait for the banner. It says the cove replaced the fishing dock — same hours, better total.

> "The dock lost its slot. Nothing was added, no fourth truck appeared. The optimizer re-solved and
> a different set fits the same eight hours better. **That** is the product."

## 2:00 – 2:20 · Looking is not cleaning — press `2`

> "A scout goes to the Quiet Inlet. Its uncertainty bonus drops because it is no longer a blind
> spot. Notice it never moved onto the truck list — 'we haven't checked' and 'send a crew' are
> different answers, and they get different lists."

## 2:20 – 2:40 · Weather drives dispatch — press `3`

Boom watch panel appears.

> "A drift scenario pushes twelve-hour landfall risk at the harbor entrance. Containment gets
> flagged before flood tide. And note the app says this one is a **loaded scenario**, not live
> weather — it will not let me pass a drill off as a forecast."

## 2:40 – 3:10 · The AI does not decide — click "Explain this dispatch"

> "Now the language model gets involved, and only now. It is handed numbers that are already final.
> Its system prompt forbids it from calculating or re-ranking anything. It writes the briefing; it
> does not choose the beaches. If it disagreed with the plan, the plan would win."

## 3:10 – 3:30 · Kill the network

Point at the source badge on the explanation.

> "There is no API key set on this machine and no Ollama running — so that explanation came from a
> local template with no model and no network at all, and the badge says exactly that. Same plan,
> same numbers, honest about who wrote the words. Three tiers: Grok, local Ollama, then this."

Close:

> "Deterministic engine, live environmental data, an exact optimum, and a model that is explicitly
> not allowed to touch the decision."

---

## If a judge asks

**"Is this just an LLM wrapper?"** — No. Remove the model entirely and the output is byte-identical;
the tests prove the engine is pure. The model writes prose after the fact.

**"Is it really a bandit?"** — Not classical UCB1. There is no repeated arm-pull reward signal. It
is an uncertainty-aware triage score using a UCB-shaped exploration term, and the code says so in
its own docstring.

**"Where do the dollar figures come from?"** — The town types them in. They are operations estimates
and every screen labels them as such. The EPA/NOAA figures on the landing page are attributed and
describe the region, not this town.

**"Can I subtract value protected from operating cost?"** — No, and the UI says so. Value protected
is an hourly exposure rate; operating cost is a whole-shift total. Different units.

**"What if the wind data is wrong?"** — Then the forecast term is wrong and the allocation shifts.
That is why it is one of two signals rather than the only one, and why the risk figure is presented
as a heuristic overlay rather than a prediction.

**"Summarize the current state."** — `GET /api/briefing` returns a plain-text shift briefing you can
read aloud.
