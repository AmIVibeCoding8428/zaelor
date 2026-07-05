import { formatINR } from "../../lib/format";

function Fact({ label, value }) {
  return (
    <div>
      <p className="text-xs text-secondary mb-1">{label}</p>
      <p className="text-sm text-text font-medium">{value}</p>
    </div>
  );
}

export default function ProfileSummary({ userInput, yearsToRetirement }) {
  return (
    <section id="profile-summary" className="mb-12 scroll-mt-8">
      <h2 className="text-xs uppercase tracking-[0.18em] text-gold mb-4">Profile Summary</h2>
      <div className="group rounded-3xl border border-white/[0.06] bg-card px-9 py-8 grid grid-cols-2 sm:grid-cols-4 gap-6 transition-all duration-500 ease-out hover:border-gold/15">
        <Fact label="Current Age" value={userInput.age} />
        <Fact label="Retirement Age" value={userInput.target_retirement_age} />
        <Fact label="Years to Retirement" value={yearsToRetirement} />
        <Fact label="Risk Appetite" value={capitalize(userInput.risk_appetite)} />
        <Fact label="Monthly Income" value={formatINR(userInput.monthly_income)} />
        <Fact label="Monthly Expenses" value={formatINR(userInput.monthly_expenses)} />
        <Fact label="Repatriation Intent" value={userInput.repatriation_intent ? "Yes" : "No"} />
        <Fact label="TRC + Form 10F on File" value={userInput.has_trc_form10f ? "Yes" : "No"} />
      </div>
    </section>
  );
}

function capitalize(value) {
  if (!value) return "—";
  return value.charAt(0).toUpperCase() + value.slice(1);
}
