# Zaelor

**Wealth beyond borders.**

Zaelor is a cross-border wealth planning platform built for UAE-based Non-Resident Indians (NRIs). It's a no-login, anonymous, stateless tool — users get a personalized, tax-aware retirement plan without ever creating an account or submitting personal data.

🔗 **Live app:** [zaelor.vercel.app](https://zaelor.vercel.app)

---

## What it does

An NRI in the UAE enters their financial details — age, retirement goals, income, expenses, existing savings, risk appetite — and receives a complete wealth plan:

- **Recommended NRI account structure** (NRE / NRO / FCNR), with DTAA-aware tax treatment
- **Asset allocation** tailored to age, risk profile, and repatriation intent
- **Monte Carlo simulation** (10,000 scenarios) projecting probability of hitting the target retirement corpus
- **SIP plan**, including an optional annual step-up strategy
- **Recommended retirement age**, calculated by finding the age at which success probability crosses an acceptable threshold
- **Feasibility check** — if the required SIP exceeds what the user says they can invest, the app surfaces a realistic alternative (extended timeline, adjusted corpus)
- **Downloadable PDF report**, styled as an institutional wealth advisory document

No sign-up. No data stored. Every session is stateless.

---

## Architecture

Zaelor is built on a strict separation between deterministic financial logic and AI-generated prose — the two never mix.

```
User fills questionnaire (React)
        ↓
POST /generate-plan (Flask)
        ↓
Deterministic Python engines, run in order:
   1. Tax & Account Engine   → NRE/NRO/FCNR recommendations, DTAA-adjusted TDS rates
   2. Asset Allocation Engine → % split across asset classes
   3. Monte Carlo Engine      → 10,000 simulated market paths
   4. SIP Engine              → required monthly SIP, feasibility check, step-up modeling
        ↓
Structured JSON (numbers, allocations, risk flags — all rule-based)
        ↓
Claude API — writes the client-facing prose explanation ONLY.
Explicit system prompt: "Do not change any numbers."
        ↓
Dashboard renders JSON + AI memo
        ↓
POST /generate-report → reuses the same plan, generates a PDF (no recompute, no re-prompt)
```

**Why this matters:** the financial engine is entirely deterministic Python — auditable, reproducible, and testable. Claude's only role is turning finished numbers into a readable narrative. It never calculates or decides anything financial.

---

## Tech stack

**Frontend:** React (Vite), Tailwind CSS, Motion (Framer Motion), Recharts, React CountUp, Lucide React
**Backend:** Python, Flask, NumPy (Monte Carlo simulation), ReportLab (PDF generation)
**AI:** Claude API (Sonnet), used exclusively for the client-facing advisory memo
**Deployment:** Vercel (frontend) · Render (backend)

---

## Key engineering details

- **10,000-path Monte Carlo simulation** with a fixed seed for reproducible results given identical inputs
- **Deterministic risk flags** — surfaced by rule-based logic (e.g. NRO repatriation caps, DTAA assumption caveats), never invented by the AI layer
- **SIP step-up modeling** — compares a flat SIP against a 5%-annual-increase alternative and reports the probability uplift
- **PDF export** — custom-built with ReportLab: vector charts (not rasterized), embedded EB Garamond + Inter font instances for print-quality typography, A4/US Letter safe margins, and a cover page matching the app's live branding
- **CORS locked down** to production + local dev origins, with an anchored regex for Vercel preview deployments (no subdomain-spoofing risk)

### A bug worth mentioning

During development, an internal check surfaced that "Probability of Success" and "Monthly SIP Required" were silently computed against two different investment amounts — the simulation was using the user's stated *feasible* budget rather than the *actual recommended SIP*, which meant every plan could show a misleadingly high success probability. It's fixed: both metrics now consistently reference the same number.

---

## Disclaimer

Zaelor is an educational planning tool, not licensed financial or tax advice. Every generated report includes the following disclaimer:

> This report is generated using assumptions based on publicly available information and user-provided inputs. It is intended for educational purposes and should not be considered personalized financial or tax advice.

Monte Carlo projections are probabilistic estimates, not guarantees. Tax, FEMA, and DTAA treatment referenced in the app reflects general rules understood at the time of writing and may not apply to every individual circumstance — users should consult a qualified advisor before acting on any output.

---

## Running locally

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL` in `frontend/.env` to point at your local backend, and `ANTHROPIC_API_KEY` in `backend/.env` for memo generation.

---

## Author

Built by [Aarav Khatri](https://github.com/AmIVibeCoding8428).
