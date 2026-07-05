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

## Visual direction — quiet-confidence luxury fintech, NOT a trading/crypto dashboard
**Exact palette (do not deviate, gold used sparingly, white is the primary text color):**
- Background: `#080808`
- Cards: `#0F0F0F`
- Gold accent: `#C9A34E` — reserved ONLY for: the wordmark's subtle underglow accent, the CTA button, and key numbers/metrics (KPI values, gold line in charts). Gold is rare everywhere else.
- Text (primary): `#FFFFFF`
- Secondary text: `#9A9A9A`

**Font:** One family, app-wide, no exceptions — **Sora**, loaded via the Google Fonts `<link>` in `frontend/index.html` and set as `--font-sans` in `frontend/src/index.css`. There is no separate display font for the wordmark anymore: the "Zaelor" wordmark renders in Sora at a large, bold, tightly-tracked weight, with a restrained gold radial underglow (`.gold-underglow` in `index.css`) behind it rather than the wordmark itself being solid gold or two-tone. (The earlier Archivo Black display-font exception and the two-tone "Zael**o**r" treatment are retired — do not reintroduce them.)

**Design brief to follow:**
"Quiet confidence. Old money meets modern technology. Luxury through restraint." Near-pure black background, white as the primary text color, gold used sparingly and deliberately. Extremely generous whitespace, minimal borders (`border-white/[0.06]` rather than `border-white/10`), subtle shadows, soft radial lighting, smooth premium animation, zero clutter. Typography is the hero — very large, bold, elegant headline treatment with tight tracking.

References: Apple, Linear, Vercel, Raycast, Notion AI, Goldman Sachs Private Wealth, luxury car configurators (Ferrari/Aston Martin/Porsche). Explicitly avoid: crypto/trading dashboard tropes (glowing green/red, dense tickers, network-mesh graphics, Web3 nav items like "Smart Contracts"/"Whitepaper"), and avoid a typical card-heavy SaaS landing page feel.

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
Cinematic, minimal, restrained — not a typical card-heavy SaaS landing page.
1. **Hero:** large centered "ZAELOR" wordmark (Sora, bold, tight tracking) + "Wealth Beyond Borders." subtitle + "AI-powered cross-border wealth planning for global Indians." supporting line + ONE gold-filled CTA ("Generate Wealth Plan", glow only on hover). Behind it: a soft, slow-drifting gold mesh, subtle floating gold particles, and a radial gold underglow behind the wordmark — alive but never distracting. Load sequence: background → logo → subtitle → CTA → mesh/particles ambient loop, no sudden movements.
2. **Three-pillar section** (replaces the old 3 feature cards — no card borders/backgrounds): large-typography Apple-product-page-style rows for Tax-Aware Allocation / Monte Carlo Simulation / Cross-Border Wealth Planning, each with an index number, a big heading, and one line of supporting copy.
3. Dashboard preview (shown large in a browser-frame mockup, real Dashboard components with sample data — don't undersell it)
4. One CTA repeated: "Generate Wealth Plan"

No testimonials, no full marketing site, no Web3-style nav, no feature cards.

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
