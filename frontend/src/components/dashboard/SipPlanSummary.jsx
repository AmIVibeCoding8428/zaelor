import { motion } from "motion/react";
import { formatINR } from "../../lib/format";

function InfoCard({ label, value, sub }) {
  return (
    <div className="min-w-0 rounded-2xl border border-white/[0.06] bg-white/[0.02] px-5 py-5">
      <p className="text-xs uppercase tracking-[0.14em] text-secondary mb-2 break-words">{label}</p>
      <p className="text-base sm:text-lg font-semibold text-text tracking-tight break-words">{value}</p>
      {sub && <p className="mt-1 text-xs text-secondary break-words">{sub}</p>}
    </div>
  );
}

function requiredAction(sipPlan) {
  if (sipPlan?.feasibility_status !== "not_feasible") {
    return "Stay the course — your current SIP is on track to reach your target.";
  }
  const suggestion = sipPlan?.alternative_suggestion;
  if (suggestion?.type === "extend_timeline") {
    return `Extend your investment horizon by ${suggestion.extra_years} year(s) to close the gap.`;
  }
  if (suggestion?.type === "reduce_corpus") {
    return `Recalibrate your target corpus to ${formatINR(suggestion.adjusted_corpus)} at your current SIP.`;
  }
  return "Increase your monthly SIP to close the gap to your target.";
}

export default function SipPlanSummary({ sipPlan, monteCarlo }) {
  const total = sipPlan?.monthly_sip_required?.total ?? 0;
  const byAssetClass = sipPlan?.monthly_sip_required?.by_asset_class ?? {};
  const entries = Object.entries(byAssetClass).sort((a, b) => b[1] - a[1]);

  const currentSip = sipPlan?.monthly_feasible_investment_amount;
  const gap = currentSip != null ? total - currentSip : null;

  const probability = monteCarlo?.probability_of_success;

  const stepUp = sipPlan?.sip_step_up;

  return (
    <section id="sip-planner" className="scroll-mt-8">
      <div className="group rounded-3xl border border-white/[0.06] bg-card px-7 sm:px-10 py-9 transition-all duration-500 ease-out hover:border-gold/15">
        <div className="flex items-start gap-5 mb-2">
          <span className="text-sm font-medium text-gold shrink-0 mt-1">02</span>
          <div>
            <h2 className="text-xs uppercase tracking-[0.18em] text-gold mb-3">
              Recommendation — SIP Plan &amp; Feasibility
            </h2>
            <p className="text-3xl sm:text-4xl font-bold tracking-tight text-gold">
              {formatINR(total)}
              <span className="text-sm text-secondary font-normal"> /month</span>
            </p>
            {total < 1 && (
              <p className="mt-1 text-xs text-secondary italic">
                Your existing assets are already projected to meet your target corpus without further contributions.
              </p>
            )}
            {stepUp && (
              <p className="mt-3 text-sm text-secondary">
                Step up <span className="text-gold font-semibold">{stepUp.annual_step_up_pct}%</span> a year and you
                could start at <span className="text-text font-medium">{formatINR(stepUp.starting_monthly_sip)}</span>
                {stepUp.projected_benefit != null && (
                  <>
                    {" "}
                    — projected{" "}
                    <span className="text-gold font-semibold">
                      {stepUp.projected_benefit >= 0 ? "+" : ""}
                      {stepUp.projected_benefit} pts
                    </span>{" "}
                    on probability of success.
                  </>
                )}
              </p>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 mt-7 mb-8">
          <InfoCard label="Current Plan" value={currentSip != null ? formatINR(currentSip) : "—"} sub="per month" />
          <InfoCard label="Recommended Plan" value={formatINR(total)} sub="per month" />
          <InfoCard
            label="Gap"
            value={gap != null ? formatINR(Math.max(gap, 0)) : "—"}
            sub={gap != null && gap <= 0 ? "already covered" : "additional needed"}
          />
          <InfoCard
            label="Success Probability"
            value={probability != null ? `${probability}%` : "—"}
            sub="Monte Carlo"
          />
          <InfoCard label="Required Action" value={sipPlan?.feasibility_status === "not_feasible" ? "Adjust plan" : "Stay the course"} />
        </div>

        <p className="text-sm text-secondary leading-relaxed mb-8 max-w-2xl">{requiredAction(sipPlan)}</p>

        <div className="space-y-5 border-t border-white/[0.06] pt-7">
          {entries.map(([assetClass, amount]) => {
            const pct = total > 0 ? (amount / total) * 100 : 0;
            return (
              <div key={assetClass}>
                <div className="flex items-center justify-between text-sm mb-2">
                  <span className="text-secondary">{assetClass}</span>
                  <span className="text-text font-medium tabular-nums">{formatINR(amount)}</span>
                </div>
                <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                  <motion.div
                    className="h-full rounded-full bg-gold"
                    initial={{ width: 0 }}
                    whileInView={{ width: `${pct}%` }}
                    viewport={{ once: true, amount: 0.6 }}
                    transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
