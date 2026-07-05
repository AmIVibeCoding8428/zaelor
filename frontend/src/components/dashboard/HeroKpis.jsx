import CountUpImport from "react-countup";
import { Target, Wallet, CalendarClock } from "lucide-react";

// react-countup ships as CJS; under Vite's dep pre-bundling the default
// import can resolve to the whole exports object instead of the component.
const CountUp = CountUpImport.default ?? CountUpImport;

function crores(amount) {
  return Number(amount) / 1e7;
}

function HeroCard({ eyebrow, value, decimals = 1, suffix = "", prefix = "", hint }) {
  return (
    <div className="group relative overflow-hidden rounded-3xl border border-white/[0.06] glass-surface px-8 py-12 sm:px-12 sm:py-16 transition-all duration-500 ease-out hover:border-gold/25">
      <div aria-hidden="true" className="glass-noise absolute inset-0 pointer-events-none" />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -left-24 -top-24 h-64 w-64 rounded-full opacity-60"
        style={{ background: "radial-gradient(closest-side, rgba(201,163,78,0.10), transparent 72%)" }}
      />
      <p className="relative text-xs uppercase tracking-[0.22em] text-secondary mb-5">{eyebrow}</p>
      <p className="relative font-bold tracking-tight text-gold text-[3.75rem] leading-none sm:text-8xl">
        {prefix}
        <CountUp end={value} decimals={decimals} duration={1.6} separator="," />
        {suffix}
      </p>
      {hint && <p className="relative mt-5 text-sm text-secondary">{hint}</p>}
    </div>
  );
}

function SecondaryCard({ eyebrow, value, decimals = 0, suffix = "", prefix = "", icon: Icon }) {
  return (
    <div className="group relative overflow-hidden rounded-2xl border border-white/[0.06] bg-card px-6 py-7 transition-all duration-500 ease-out hover:-translate-y-0.5 hover:border-gold/15">
      <div className="relative flex items-center justify-between mb-4">
        <p className="text-[11px] uppercase tracking-[0.16em] text-secondary">{eyebrow}</p>
        {Icon && <Icon size={15} className="text-secondary/50 shrink-0" />}
      </div>
      <p className="relative font-semibold tracking-tight text-text text-3xl">
        {prefix}
        <CountUp end={value} decimals={decimals} duration={1.4} separator="," />
        {suffix}
      </p>
    </div>
  );
}

export default function HeroKpis({ plan, userInput }) {
  const probability = plan.monte_carlo?.probability_of_success ?? 0;
  const targetCorpus = userInput.target_retirement_corpus ?? 0;
  const monthlySip = plan.sip_plan?.monthly_sip_required?.total ?? 0;
  const retirementAge = Number(userInput.target_retirement_age ?? 0);
  const numSimulations = plan.monte_carlo?.num_simulations;

  return (
    <section id="hero" className="mb-14 scroll-mt-8">
      <div className="grid grid-cols-1 gap-6 mb-6">
        <HeroCard
          eyebrow="Probability of Success"
          value={probability}
          decimals={1}
          suffix="%"
          hint={numSimulations ? `Across ${numSimulations.toLocaleString()} simulated market scenarios.` : undefined}
        />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <SecondaryCard eyebrow="Target Corpus" value={crores(targetCorpus)} decimals={2} prefix="₹" suffix=" Cr" icon={Target} />
        <SecondaryCard eyebrow="Monthly SIP Required" value={monthlySip} decimals={0} prefix="₹" icon={Wallet} />
        <SecondaryCard eyebrow="Retirement Age" value={retirementAge} icon={CalendarClock} />
      </div>
    </section>
  );
}
