# Zaelor — Project Context

## What this is
Zaelor ("Wealth Beyond Borders") is a full-stack NRI wealth planning web app, focused exclusively on **UAE-based NRIs**. It's a no-login, anonymous, stateless tool — users get a personalized wealth plan without ever signing up or submitting personal data.

**Tagline:** "Zaelor — Wealth beyond borders."

## Core purpose
An NRI in the UAE inputs their financial details (age, retirement goals, income, expenses, savings, risk appetite) and gets back a complete, tax-aware wealth plan: recommended asset allocation, monthly SIP required, and probability of hitting their target retirement corpus — all backed by a Monte Carlo simulation.

## Tech stack
- **Frontend:** React, Tailwind CSS, Motion (Framer Motion), Recharts, React CountUp, Lucide React → deployed on **Vercel** (free tier)
- **Backend:** Python, Flask → deployed on **Render** free tier ($0 ongoing cost; spins down after 15 min inactivity, ~30-60 sec cold start on wake — acceptable since app is stateless anyway)
- **PDF generation:** ReportLab, generated backend-side only, never in React
- **AI layer:** Claude API — used ONLY to convert structured JSON output into professional prose. Claude never calculates or decides financial logic.

## Architecture (strict separation — do not blur this)
1. User fills questionnaire in React → `POST /generate-plan` → Flask
2. Flask runs deterministic Python engines, in order:
   - **Tax & Account Layer** — NRE/NRO/FCNR account guidance, TDS/capital gains rules for NRIs, DTAA treatment (India-UAE)
   - **Asset Allocation Engine** — recommends % split across Indian Equity, International ETFs, Indian Debt, Gold (SGB), REITs/Real Estate, Cash, based on age/risk profile/repatriation intent
   - **Monte Carlo Simulation** — runs 10,000 scenarios, outputs probability of hitting target corpus + best/median/worst case
   - **SIP Calculator** — computes monthly SIP required, split across asset classes
   - **Feasibility check** — compares required SIP against user's stated "feasible investment amount"; if required > feasible, surface a realistic nearby alternative (adjusted corpus / timeline / risk profile)
3. All of the above outputs **structured JSON only** (numbers, allocations, risk flags — risk flags are also rule-based, not AI-generated)
4. Flask then calls the Claude API with that JSON and a strict prompt: *"Write a professional wealth advisory summary for an NRI client based on this JSON. Do not change any numbers."*
5. Flask returns JSON + Claude's memo together → React renders the dashboard
6. PDF export is a **separate endpoint** (`POST /generate-report`) → Flask generates PDF via ReportLab → returns file for download

**Interview framing (keep this true in the code):** "The financial engine is entirely deterministic Python. Claude is only used to generate the client-facing explanation."

## CORS (do not forget)
Flask must explicitly enable CORS for the Vercel frontend origin:
```python
from flask_cors import CORS
CORS(app, origins=["https://your-vercel-url.vercel.app"])
```

## Visual direction — premium private banking portal, NOT a trading/crypto dashboard
**Exact palette (do not deviate, single gold accent only):**
- Background: `#0A0A0A`
- Cards: `#111111`
- Gold accent: `#C8A24C`
- Text: `#F5F5F5`
- Secondary text: `#A1A1A1`

**Font:** One family only — Inter or Satoshi.

**Design brief to follow:**
"Do not design this like a trading dashboard. Design it like a premium private banking portal. Use generous whitespace, strong visual hierarchy, large typography for key metrics, subtle gold accents, minimal borders, soft shadows, and smooth Motion animations. Every component should prioritize readability over decoration."

References: Apple (spacing), Linear (clean cards), Bloomberg (finance density where needed), Julius Baer/Rothschild (luxury feel). Explicitly avoid: crypto/trading dashboard tropes (glowing green/red, dense tickers, network-mesh graphics, Web3 nav items like "Smart Contracts"/"Whitepaper").

## Layout
**Sidebar:** Dashboard, Profile Summary, Asset Allocation, SIP Planner, Monte Carlo Analysis, Tax & FEMA, Reports. Include a "100% Anonymous / No login / No personal data" trust badge.

**Dashboard hero KPIs (in order of visual importance):**
1. Probability of Success (biggest, most prominent)
2. Target Corpus
3. Monthly SIP Required
4. Retirement Age

**Center:** One dominant chart — 25-year Projected Net Worth (median/best/worst case lines)

**Below:** Uniform, simple asset allocation cards (Indian Equity, International ETF, Debt, Gold, Cash) — same size/weight, not competing for attention

**Bottom:** Dense Bloomberg-terminal-style table (Asset / Allocation / Monthly SIP / Expected Return) — acceptable to be denser than the rest of the UI

**Quick Insights panel:** Advisory-style takeaways, e.g. "Increase SIP by ₹X/month to improve probability to Y%" — generated from deterministic logic + Claude prose, not invented by Claude.

## Homepage (keep minimal — this is a tool, not a SaaS marketing site)
1. Hero: "Zaelor" wordmark + "Wealth beyond borders." tagline
2. 3 feature cards: tax-aware allocation, Monte Carlo probability, no-login privacy
3. Dashboard preview (shown large — don't undersell it)
4. One CTA: "Generate Wealth Plan"

No testimonials, no full marketing site, no Web3-style nav.

## Animation polish (once core logic works — don't front-load this)
- Donut chart draws in on load
- KPI numbers count up (React CountUp)
- Staggered card fade-ins (~0.08s stagger)
- 200–350ms ease-out durations
- No bouncy/flashy effects
- Optional: sequential "Processing..." checkmark animation on report generation (~3-5 sec) — steps must match what's actually being computed

## Input fields (questionnaire)
- Age, target retirement age
- Country of residence: UAE only (v1 scope)
- Monthly income
- Monthly expenses
- Monthly feasible investment amount (user self-declared)
- Existing assets (Indian + foreign)
- Risk appetite (conservative/moderate/aggressive)
- Target retirement corpus (INR)
- Repatriation intent (yes/no)

## Mandatory PDF disclaimer
Must appear at the bottom of every generated PDF:

> "This report is generated using assumptions based on publicly available information and user-provided inputs. It is intended for educational purposes and should not be considered personalized financial or tax advice."

## Stretch goals (only after core v1 works — do not let these block the deadline)
1. One-line rationale per allocation (deterministic Python generates the reason, Claude writes the sentence)
2. Side-by-side strategy comparison (aggressive vs conservative — just re-run engines with different risk_profile)
3. Assumptions & Limitations section near the disclaimer (expected returns, inflation rate, tax year assumed)
4. PDF with full gold/black design treatment — should feel like an RM handout

**Explicitly excluded from scope:** stress-testing (high inflation / weaker INR / delayed retirement scenarios) — too much scope risk for the timeline.

## API keys & secrets
- Claude API key goes in Render's environment variables — **never in code, never committed to git**
- Frontend connects to backend via an env var (e.g. `VITE_API_URL`) set in Vercel project settings

## Priorities, in order
1. Get the 4 engines actually calculating correct numbers first
2. Get the JSON → Claude memo → dashboard render pipeline working end-to-end
3. Then layer in visual polish and animations
4. Stretch goals only if time allows before the deadline
