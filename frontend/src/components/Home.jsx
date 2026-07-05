import { useMemo, useRef } from "react";
import { motion, useScroll, useTransform } from "motion/react";
import { ArrowRight } from "lucide-react";
import HeroKpis from "./dashboard/HeroKpis";
import NetWorthChart from "./dashboard/NetWorthChart";
import AllocationDonut from "./dashboard/AllocationDonut";
import SipPlanSummary from "./dashboard/SipPlanSummary";

const EASE_OUT = [0.16, 1, 0.3, 1];

const NAV_LINKS = [
  { label: "Product", href: "#product" },
  { label: "How It Works", href: "#pillars" },
  { label: "Privacy", href: "#trust" },
  { label: "About", href: "#top" },
];

const PILLARS = [
  {
    index: "01",
    title: "Tax-Aware Allocation",
    copy: "NRE, NRO, FCNR and DTAA — mapped into a portfolio that keeps what the tax code lets you keep.",
  },
  {
    index: "02",
    title: "Monte Carlo Simulation",
    copy: "10,000 simulated futures, one honest probability of reaching the number you actually need.",
  },
  {
    index: "03",
    title: "Cross-Border Wealth Planning",
    copy: "Built for Indians living in the UAE — one plan that moves the way your life does.",
  },
];

// Static sample data — purely illustrative, shown on the homepage preview only.
const SAMPLE_PLAN = {
  monte_carlo: {
    probability_of_success: 87.4,
    num_simulations: 10000,
    median_case: Array.from({ length: 20 }, (_, i) => 8_500_000 * Math.pow(1.11, i)),
    best_case: Array.from({ length: 20 }, (_, i) => 8_500_000 * Math.pow(1.17, i)),
    worst_case: Array.from({ length: 20 }, (_, i) => 8_500_000 * Math.pow(1.05, i)),
  },
  asset_allocation: {
    years_to_retirement: 20,
    allocations: {
      "Indian Equity": 40,
      "International ETFs": 20,
      "Indian Debt": 20,
      "Gold (SGB)": 10,
      "REITs": 5,
      "Cash": 5,
    },
  },
  sip_plan: {
    monthly_sip_required: {
      total: 185000,
      by_asset_class: {
        "Indian Equity": 74000,
        "International ETFs": 37000,
        "Indian Debt": 37000,
        "Gold (SGB)": 18500,
        "Cash": 18500,
      },
    },
    monthly_feasible_investment_amount: 150000,
    feasibility_status: "not_feasible",
    alternative_suggestion: null,
    sip_step_up: {
      annual_step_up_pct: 5,
      starting_monthly_sip: 148000,
      flat_monthly_sip_required: 185000,
      probability_of_success_with_stepup: 91.2,
      probability_of_success_without_stepup: 87.4,
      projected_benefit: 3.8,
    },
  },
};

const SAMPLE_USER_INPUT = {
  target_retirement_corpus: 60000000,
  target_retirement_age: 55,
};

// Slow, drifting gold mesh — a handful of soft blurred blobs, never sharp,
// never bright enough to read as "glowing" rather than "ambient."
function GoldMesh() {
  return (
    <div aria-hidden="true" className="pointer-events-none absolute inset-0 overflow-hidden">
      <motion.div
        className="absolute -left-1/4 top-0 h-[600px] w-[600px] rounded-full blur-[120px]"
        style={{ background: "radial-gradient(closest-side, rgba(201,163,78,0.14), transparent 70%)" }}
        animate={{ x: [0, 60, -20, 0], y: [0, 40, -20, 0] }}
        transition={{ duration: 28, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute right-[-10%] top-1/4 h-[520px] w-[520px] rounded-full blur-[130px]"
        style={{ background: "radial-gradient(closest-side, rgba(201,163,78,0.10), transparent 70%)" }}
        animate={{ x: [0, -50, 30, 0], y: [0, -30, 20, 0] }}
        transition={{ duration: 32, repeat: Infinity, ease: "easeInOut" }}
      />
    </div>
  );
}

function GoldParticles() {
  const particles = useMemo(
    () =>
      Array.from({ length: 16 }, (_, i) => ({
        id: i,
        left: Math.random() * 100,
        size: 1.5 + Math.random() * 2.5,
        delay: 1.6 + Math.random() * 6,
        duration: 8 + Math.random() * 6,
        drift: (Math.random() - 0.5) * 30,
      })),
    []
  );

  return (
    <div aria-hidden="true" className="pointer-events-none absolute inset-0 overflow-hidden">
      {particles.map((p) => (
        <motion.span
          key={p.id}
          className="absolute rounded-full bg-gold"
          style={{
            left: `${p.left}%`,
            bottom: "8%",
            width: p.size,
            height: p.size,
            opacity: 0,
          }}
          animate={{
            opacity: [0, 0.4, 0],
            y: [0, -140 - Math.random() * 80],
            x: [0, p.drift],
          }}
          transition={{
            duration: p.duration,
            delay: p.delay,
            repeat: Infinity,
            ease: "easeOut",
          }}
        />
      ))}
    </div>
  );
}

function CtaButton({ onGenerate, children, className = "" }) {
  return (
    <button
      onClick={onGenerate}
      className={`group relative inline-flex items-center gap-2.5 rounded-full bg-gold px-9 py-4 text-[15px] font-semibold text-black transition-all duration-500 ease-out hover:shadow-[0_0_44px_rgba(201,163,78,0.4)] hover:-translate-y-0.5 ${className}`}
    >
      {children}
      <ArrowRight size={17} className="transition-transform duration-300 ease-out group-hover:translate-x-1" />
    </button>
  );
}

// Sticky top nav — translucent, blurred, deliberately quiet so it never
// competes with the hero sitting beneath it.
function SiteNav({ onGenerate }) {
  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-white/[0.06] bg-background/60 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <a href="#top" className="text-sm font-bold tracking-tight text-text">
          ZAELOR
        </a>

        <nav className="hidden items-center gap-9 md:flex">
          {NAV_LINKS.map((link) => (
            <a
              key={link.label}
              href={link.href}
              className="text-[13px] font-medium text-secondary transition-colors duration-300 ease-out hover:text-text"
            >
              {link.label}
            </a>
          ))}
        </nav>

        <button
          onClick={onGenerate}
          className="rounded-full border border-gold/40 px-5 py-2 text-[13px] font-semibold text-gold transition-all duration-300 ease-out hover:bg-gold hover:text-black hover:shadow-[0_0_28px_rgba(201,163,78,0.3)]"
        >
          Start Planning
        </button>
      </div>
    </header>
  );
}

// Fades + scales the hero down as the user scrolls it out of view — the
// "receding" half of the hero-to-pillars transition. The scroll-target ref
// sits on a plain (non-motion) wrapper so framer's scroll tracking never
// shares a node with the animated element — keeping this fully independent
// of each child's own mount-in animation.
function ScrollExit({ children, className }) {
  const ref = useRef(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start start", "end start"] });
  const opacity = useTransform(scrollYProgress, [0, 1], [1, 0.1]);
  const scale = useTransform(scrollYProgress, [0, 1], [1, 0.92]);

  return (
    <div ref={ref}>
      <motion.div style={{ opacity, scale }} className={className}>
        {children}
      </motion.div>
    </div>
  );
}

// Fades + scales a section in as it enters the viewport and gently recedes
// as it's scrolled past — the "incoming section replaces the last one" feel.
// `noScale` skips the transform: combining a scale ancestor with a
// backdrop-filter descendant (the KPI cards' glass-surface) triggers a
// Chromium compositing bug that blacks out the whole layer, so sections
// containing glass-surface cards use opacity-only movement.
function ScrollRecede({ children, className, noScale }) {
  const ref = useRef(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start end", "center center", "end start"] });
  const opacity = useTransform(scrollYProgress, [0, 0.5, 1], [0.2, 1, 0.2]);
  const scale = useTransform(scrollYProgress, [0, 0.5, 1], [0.95, 1, 0.95]);

  return (
    <div ref={ref}>
      <motion.div style={noScale ? { opacity } : { opacity, scale }} className={className}>
        {children}
      </motion.div>
    </div>
  );
}

// Shrinks the sample dashboard ~30%. Uses `zoom` rather than a CSS
// `transform: scale()` — transforms are paint-only and don't shrink the
// layout box, which would leave a large dead gap below the visibly-smaller
// content; `zoom` shrinks the box itself, so the page flows correctly.
function ScaledDashboardPreview({ children }) {
  return <div style={{ zoom: 0.7 }}>{children}</div>;
}

export default function Home({ onGenerate }) {
  return (
    <div id="top" className="min-h-screen bg-background">
      <SiteNav onGenerate={onGenerate} />

      {/* Hero — occupies exactly one viewport. Wordmark, tagline, supporting
          copy and the primary CTA are the only things visible on load. */}
      <ScrollExit className="relative flex h-screen min-h-[720px] flex-col items-center justify-center px-6 text-center overflow-hidden">
        <GoldMesh />
        <GoldParticles />

        <div aria-hidden="true" className="gold-underglow pointer-events-none absolute left-1/2 top-[42%] -z-10 h-[420px] w-[620px] -translate-x-1/2 -translate-y-1/2" />

        <motion.h1
          className="relative text-7xl sm:text-9xl font-extrabold tracking-[-0.03em] text-text"
          style={{ textShadow: "0 0 60px rgba(201,163,78,0.18)" }}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.15, ease: EASE_OUT }}
        >
          ZAELOR
        </motion.h1>

        <motion.p
          className="mt-8 text-xl sm:text-2xl font-medium text-text/90"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.65, ease: EASE_OUT }}
        >
          Wealth Beyond Borders.
        </motion.p>

        <motion.p
          className="mt-4 max-w-md text-sm sm:text-base text-secondary"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.85, ease: EASE_OUT }}
        >
          AI-powered cross-border wealth planning for global Indians.
        </motion.p>
      </ScrollExit>

      {/* Floating dashboard preview — an Apple-product-page style panel:
          slight perspective tilt, layered shadow, glass border, soft
          ambient float. Fades in, then settles from 98% to 100% scale. */}
      <section id="product" className="px-6 pt-28 pb-20 sm:pt-36 sm:pb-28 scroll-mt-24">
        <div className="mx-auto max-w-6xl">
          <p className="mb-10 text-center text-sm font-medium text-secondary">Your dashboard, ready in seconds.</p>

          <div className="relative" style={{ perspective: 1600 }}>
            <div
              aria-hidden="true"
              className="absolute inset-x-16 -bottom-8 h-20 rounded-full bg-black/70 blur-3xl"
            />

            <motion.div
              initial={{ opacity: 0, scale: 0.98, rotateX: 8 }}
              whileInView={{ opacity: 1, scale: 1, rotateX: 3 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{
                opacity: { duration: 0.6, ease: EASE_OUT },
                scale: { duration: 0.9, delay: 0.15, ease: EASE_OUT },
                rotateX: { duration: 0.9, delay: 0.15, ease: EASE_OUT },
              }}
            >
              <motion.div
                animate={{ y: [0, -8, 0] }}
                transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
                className="rounded-[28px] border border-white/[0.08] bg-card/90 backdrop-blur-xl overflow-hidden shadow-[0_30px_80px_-20px_rgba(0,0,0,0.65),0_60px_140px_-30px_rgba(0,0,0,0.5)]"
              >
                <div className="flex items-center gap-1.5 border-b border-white/[0.06] px-6 py-4">
                  <span className="h-2.5 w-2.5 rounded-full bg-white/10" />
                  <span className="h-2.5 w-2.5 rounded-full bg-white/10" />
                  <span className="h-2.5 w-2.5 rounded-full bg-white/10" />
                </div>
                <div className="pointer-events-none select-none px-6 sm:px-12 py-12 bg-background">
                  <motion.div
                    initial={{ opacity: 0, y: 12 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true, amount: 0.3 }}
                    transition={{ duration: 0.6, delay: 0.6, ease: EASE_OUT }}
                  >
                    <ScaledDashboardPreview>
                      <HeroKpis plan={SAMPLE_PLAN} userInput={SAMPLE_USER_INPUT} />
                    </ScaledDashboardPreview>
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, y: 12 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true, amount: 0.3 }}
                    transition={{ duration: 0.6, delay: 0.35, ease: EASE_OUT }}
                  >
                    <ScaledDashboardPreview>
                      <NetWorthChart monteCarlo={SAMPLE_PLAN.monte_carlo} />
                    </ScaledDashboardPreview>
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, y: 12 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true, amount: 0.3 }}
                    transition={{ duration: 0.6, delay: 0.8, ease: EASE_OUT }}
                  >
                    <ScaledDashboardPreview>
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <AllocationDonut assetAllocation={SAMPLE_PLAN.asset_allocation} />
                        <SipPlanSummary sipPlan={SAMPLE_PLAN.sip_plan} monteCarlo={SAMPLE_PLAN.monte_carlo} />
                      </div>
                    </ScaledDashboardPreview>
                  </motion.div>
                </div>
              </motion.div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Trust section — typography only, directly after the dashboard. */}
      <section id="trust" className="px-6 pb-28 sm:pb-32 scroll-mt-24">
        <motion.div
          className="mx-auto max-w-3xl text-center"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.5 }}
          transition={{ duration: 0.7, ease: EASE_OUT }}
        >
          <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight text-text">
            Built for Indian professionals managing wealth across borders.
          </h2>
          <p className="mt-5 text-xs sm:text-sm uppercase tracking-[0.2em] text-secondary">
            UAE &bull; India &bull; NRE &bull; NRO &bull; FCNR &bull; DTAA &bull; Monte Carlo Analysis
          </p>
        </motion.div>
      </section>

      <ScrollRecede className="px-6 pb-20 sm:pb-28 scroll-mt-24" >
        <div id="pillars" className="mx-auto max-w-5xl">
          {PILLARS.map((p, i) => (
            <motion.div
              key={p.title}
              className={`flex flex-col sm:flex-row sm:items-baseline gap-4 sm:gap-12 py-14 ${
                i !== 0 ? "border-t border-white/[0.06]" : ""
              }`}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.5 }}
              transition={{ duration: 0.7, delay: i * 0.08, ease: EASE_OUT }}
            >
              <span className="text-sm font-medium text-gold sm:w-16 shrink-0">{p.index}</span>
              <h3 className="text-3xl sm:text-4xl font-semibold tracking-tight text-text sm:w-96 shrink-0">
                {p.title}
              </h3>
              <p className="max-w-md text-base text-secondary leading-relaxed">{p.copy}</p>
            </motion.div>
          ))}
        </div>
      </ScrollRecede>

      <section className="px-6 pb-40 flex justify-center">
        <CtaButton onGenerate={onGenerate}>Build My Wealth Plan</CtaButton>
      </section>
    </div>
  );
}
