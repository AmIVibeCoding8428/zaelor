import CountUpImport from "react-countup";

const CountUp = CountUpImport.default ?? CountUpImport;

export default function RetirementAgeCard({ recommendedRetirementAge }) {
  const age = recommendedRetirementAge?.recommended_retirement_age;
  const statedAge = recommendedRetirementAge?.stated_retirement_age;
  const probability = recommendedRetirementAge?.probability_of_success;
  const meetsThreshold = recommendedRetirementAge?.meets_threshold;
  const explanation = recommendedRetirementAge?.explanation;

  if (age == null) return null;

  const isEarlier = statedAge != null && age < statedAge;
  const isLater = statedAge != null && age > statedAge;

  return (
    <div className="group rounded-3xl border border-white/[0.06] bg-card px-7 sm:px-10 py-9 transition-all duration-500 ease-out hover:border-gold/15">
      <div className="flex items-start gap-5 mb-5">
        <span className="text-sm font-medium text-gold shrink-0 mt-1">01</span>
        <div>
          <h2 className="text-xs uppercase tracking-[0.18em] text-gold mb-3">Recommendation — Retirement Age</h2>
          <p className="text-3xl sm:text-4xl font-bold tracking-tight text-text">
            Recommended Retirement Age:{" "}
            <span className="text-gold">
              <CountUp end={age} duration={1.2} />
            </span>{" "}
            Years
          </p>
        </div>
      </div>

      <p className="text-sm text-secondary leading-relaxed max-w-2xl mb-6">{explanation}</p>

      <div className="flex flex-wrap gap-8 border-t border-white/[0.06] pt-5">
        <div>
          <p className="text-xs text-secondary mb-1">Your Stated Age</p>
          <p className="text-sm text-text font-medium">{statedAge ?? "—"} Years</p>
        </div>
        <div>
          <p className="text-xs text-secondary mb-1">Probability at Recommended Age</p>
          <p className="text-sm text-text font-medium">{probability != null ? `${probability}%` : "—"}</p>
        </div>
        <div>
          <p className="text-xs text-secondary mb-1">Outlook</p>
          <p className="text-sm font-medium text-gold">
            {!meetsThreshold ? "Needs a bigger lever" : isEarlier ? "Ahead of plan" : isLater ? "Catch-up needed" : "On track"}
          </p>
        </div>
      </div>
    </div>
  );
}
