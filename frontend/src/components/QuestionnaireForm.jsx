import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Loader2, ShieldCheck } from "lucide-react";
import { formatINR, groupIndianDigits } from "../lib/format";

const API_URL = import.meta.env.VITE_API_URL;

const RISK_OPTIONS = [
  { value: "conservative", label: "Conservative" },
  { value: "moderate", label: "Moderate" },
  { value: "aggressive", label: "Aggressive" },
];

const INITIAL_FORM = {
  age: "",
  target_retirement_age: "",
  monthly_income: "",
  monthly_expenses: "",
  monthly_feasible_investment_amount: "",
  existing_indian_assets: "",
  existing_foreign_assets: "",
  risk_appetite: "moderate",
  target_retirement_corpus: "",
  repatriation_intent: null,
  has_trc_form10f: null,
};

const STEPS = [
  {
    id: "profile",
    title: "Profile & Timeline",
    validate: (f) => f.age !== "" && f.target_retirement_age !== "",
  },
  {
    id: "cashflow",
    title: "Monthly Cash Flow",
    validate: (f) =>
      f.monthly_income !== "" &&
      f.monthly_expenses !== "" &&
      f.monthly_feasible_investment_amount !== "",
  },
  {
    id: "assets",
    title: "Existing Assets",
    validate: (f) => f.existing_indian_assets !== "" && f.existing_foreign_assets !== "",
  },
  {
    id: "goals",
    title: "Risk & Goals",
    validate: (f) => !!f.risk_appetite && f.target_retirement_corpus !== "",
  },
  {
    id: "tax",
    title: "Tax & Repatriation",
    validate: (f) => f.repatriation_intent !== null && f.has_trc_form10f !== null,
  },
  {
    id: "review",
    title: "Review & Submit",
    validate: () => true,
  },
];

// Physical, weighty deceleration curve (no bounce) shared by every card in the stack.
const EASE_OUT = [0.16, 1, 0.3, 1];
const TRANSITION = { duration: 0.34, ease: EASE_OUT };

// Resting transform for a card at a given depth in the stack (0 = front).
// Peek cards (offset > 0) splay out to the sides at steep angles, like a hand
// of cards fanned open — the spread is the primary effect, not a downward peek.
function cardRest(offset) {
  return {
    opacity: offset === 0 ? 1 : offset === 1 ? 0.4 : 0.22,
    x: offset === 0 ? 0 : offset % 2 === 1 ? -72 : 88,
    y: offset * 12,
    scale: 1 - offset * 0.05,
    rotate: offset === 0 ? 0 : offset % 2 === 1 ? -16 : 19,
    zIndex: 30 - offset * 10,
  };
}

// Where a card starts from when it first mounts into the stack.
function cardEnter(offset, direction) {
  if (direction === -1 && offset === 0) {
    // Stepping back: the revisited card slides back in from the left.
    return { opacity: 0, x: -32, y: 0, scale: 1, rotate: 0, zIndex: 30 };
  }
  // Stepping forward (or first paint): the card rises quietly into the back of the stack.
  const rest = cardRest(offset);
  return { ...rest, opacity: 0, y: rest.y + (direction === 1 ? 16 : 10), scale: rest.scale - 0.05 };
}

// Where a card goes when it leaves the stack for good.
function cardLeave(direction) {
  return direction === -1
    ? { opacity: 0, y: 70, scale: 0.75, zIndex: 0 }
    : { opacity: 0, x: -70, rotate: -8, scale: 0.9, zIndex: 40 };
}

function FieldLabel({ children, hint }) {
  return (
    <label className="block mb-2">
      <span className="text-sm font-medium text-text">{children}</span>
      {hint && <span className="block text-xs text-secondary mt-0.5">{hint}</span>}
    </label>
  );
}

function NumberField({ id, label, hint, value, onChange, placeholder, prefix }) {
  const displayValue = groupIndianDigits(String(value ?? "").replace(/\D/g, ""));

  function handleChange(e) {
    onChange(e.target.value.replace(/\D/g, ""));
  }

  return (
    <div>
      <FieldLabel hint={hint}>{label}</FieldLabel>
      <div className="relative">
        {prefix && (
          <span className="absolute left-4 top-1/2 -translate-y-1/2 text-secondary text-sm">
            {prefix}
          </span>
        )}
        <input
          id={id}
          type="text"
          inputMode="numeric"
          required
          value={displayValue}
          onChange={handleChange}
          placeholder={placeholder}
          className={`w-full bg-background border border-white/10 rounded-lg py-3 ${
            prefix ? "pl-10" : "pl-4"
          } pr-4 text-text placeholder:text-secondary/60 focus:outline-none focus:border-gold/60 focus:ring-1 focus:ring-gold/40 transition-colors`}
        />
      </div>
    </div>
  );
}

function YesNoToggle({ label, hint, value, onChange }) {
  return (
    <div>
      <FieldLabel hint={hint}>{label}</FieldLabel>
      <div className="grid grid-cols-2 gap-3">
        {[
          { value: true, label: "Yes" },
          { value: false, label: "No" },
        ].map((option) => (
          <button
            key={String(option.value)}
            type="button"
            onClick={() => onChange(option.value)}
            className={`py-3 rounded-lg border text-sm font-medium transition-colors ${
              value === option.value
                ? "border-gold bg-gold/10 text-gold"
                : "border-white/10 bg-background text-secondary hover:border-white/20"
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function ReviewFact({ label, value }) {
  return (
    <div>
      <p className="text-xs text-secondary mb-1">{label}</p>
      <p className="text-sm text-text font-medium">{value}</p>
    </div>
  );
}

function StepFields({ stepId, form, update }) {
  switch (stepId) {
    case "profile":
      return (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <NumberField id="age" label="Current age" value={form.age} onChange={update("age")} placeholder="35" />
          <NumberField
            id="target_retirement_age"
            label="Target retirement age"
            value={form.target_retirement_age}
            onChange={update("target_retirement_age")}
            placeholder="60"
          />
          <div className="sm:col-span-2">
            <FieldLabel hint="v1 scope is limited to UAE-based NRIs.">Country of residence</FieldLabel>
            <div className="w-full sm:w-1/2 bg-background border border-white/10 rounded-lg py-3 px-4 text-secondary">
              UAE
            </div>
          </div>
        </div>
      );
    case "cashflow":
      return (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <NumberField
            id="monthly_income"
            label="Monthly income"
            prefix="₹"
            value={form.monthly_income}
            onChange={update("monthly_income")}
            placeholder="3,00,000"
          />
          <NumberField
            id="monthly_expenses"
            label="Monthly expenses"
            prefix="₹"
            value={form.monthly_expenses}
            onChange={update("monthly_expenses")}
            placeholder="1,50,000"
          />
          <div className="sm:col-span-2">
            <NumberField
              id="monthly_feasible_investment_amount"
              label="Monthly feasible investment amount"
              hint="How much can you realistically invest each month?"
              prefix="₹"
              value={form.monthly_feasible_investment_amount}
              onChange={update("monthly_feasible_investment_amount")}
              placeholder="1,00,000"
            />
          </div>
        </div>
      );
    case "assets":
      return (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <NumberField
            id="existing_indian_assets"
            label="Existing Indian assets"
            prefix="₹"
            value={form.existing_indian_assets}
            onChange={update("existing_indian_assets")}
            placeholder="20,00,000"
          />
          <NumberField
            id="existing_foreign_assets"
            label="Existing foreign assets"
            prefix="₹"
            value={form.existing_foreign_assets}
            onChange={update("existing_foreign_assets")}
            placeholder="5,00,000"
          />
        </div>
      );
    case "goals":
      return (
        <div>
          <div className="mb-6">
            <FieldLabel>Risk appetite</FieldLabel>
            <div className="grid grid-cols-3 gap-3">
              {RISK_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => update("risk_appetite")(option.value)}
                  className={`py-3 rounded-lg border text-sm font-medium transition-colors ${
                    form.risk_appetite === option.value
                      ? "border-gold bg-gold/10 text-gold"
                      : "border-white/10 bg-background text-secondary hover:border-white/20"
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
          <NumberField
            id="target_retirement_corpus"
            label="Target retirement corpus"
            hint="The total corpus (INR) you want to have by retirement."
            prefix="₹"
            value={form.target_retirement_corpus}
            onChange={update("target_retirement_corpus")}
            placeholder="5,00,00,000"
          />
        </div>
      );
    case "tax":
      return (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <YesNoToggle
            label="Repatriation intent"
            hint="Do you plan to move funds from India back to the UAE?"
            value={form.repatriation_intent}
            onChange={update("repatriation_intent")}
          />
          <YesNoToggle
            label="Hold TRC + Form 10F"
            hint="Tax Residency Certificate + Form 10F on file?"
            value={form.has_trc_form10f}
            onChange={update("has_trc_form10f")}
          />
        </div>
      );
    case "review":
      return (
        <div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-5">
            <ReviewFact label="Current Age" value={form.age} />
            <ReviewFact label="Retirement Age" value={form.target_retirement_age} />
            <ReviewFact label="Risk Appetite" value={capitalize(form.risk_appetite)} />
            <ReviewFact label="Monthly Income" value={formatINR(Number(form.monthly_income) || 0)} />
            <ReviewFact label="Monthly Expenses" value={formatINR(Number(form.monthly_expenses) || 0)} />
            <ReviewFact
              label="Feasible SIP"
              value={formatINR(Number(form.monthly_feasible_investment_amount) || 0)}
            />
            <ReviewFact label="Existing Indian Assets" value={formatINR(Number(form.existing_indian_assets) || 0)} />
            <ReviewFact label="Existing Foreign Assets" value={formatINR(Number(form.existing_foreign_assets) || 0)} />
            <ReviewFact label="Target Corpus" value={formatINR(Number(form.target_retirement_corpus) || 0)} />
            <ReviewFact label="Repatriation Intent" value={form.repatriation_intent ? "Yes" : "No"} />
            <ReviewFact label="TRC + Form 10F on File" value={form.has_trc_form10f ? "Yes" : "No"} />
          </div>
          <p className="mt-6 text-xs text-secondary italic">
            Use "Back" to edit any step before generating your plan.
          </p>
        </div>
      );
    default:
      return null;
  }
}

function capitalize(value) {
  if (!value) return "—";
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function StepDots({ total, current }) {
  return (
    <div className="flex items-center justify-center gap-2 mt-6">
      {Array.from({ length: total }).map((_, i) => (
        <span
          key={i}
          className={`h-1.5 rounded-full transition-all duration-300 ease-out ${
            i === current ? "w-5 bg-gold" : "w-1.5 bg-secondary/30"
          }`}
        />
      ))}
    </div>
  );
}

export default function QuestionnaireForm({ onGenerated }) {
  const [form, setForm] = useState(INITIAL_FORM);
  const [currentStep, setCurrentStep] = useState(0);
  const [direction, setDirection] = useState(0);
  const [status, setStatus] = useState("idle"); // idle | loading | success | error
  const [errorMessage, setErrorMessage] = useState("");

  const update = (field) => (value) => setForm((prev) => ({ ...prev, [field]: value }));

  const isLastStep = currentStep === STEPS.length - 1;
  const step = STEPS[currentStep];
  const canAdvance = step.validate(form);

  function goNext() {
    if (!canAdvance || currentStep >= STEPS.length - 1) return;
    setDirection(1);
    setCurrentStep((s) => s + 1);
  }

  function goBack() {
    if (currentStep === 0) return;
    setDirection(-1);
    setCurrentStep((s) => s - 1);
  }

  async function submitPlan() {
    if (status === "loading") return;

    setStatus("loading");
    setErrorMessage("");

    const payload = {
      age: Number(form.age),
      target_retirement_age: Number(form.target_retirement_age),
      country_of_residence: "UAE",
      monthly_income: Number(form.monthly_income),
      monthly_expenses: Number(form.monthly_expenses),
      monthly_feasible_investment_amount: Number(form.monthly_feasible_investment_amount),
      existing_indian_assets: Number(form.existing_indian_assets),
      existing_foreign_assets: Number(form.existing_foreign_assets),
      risk_appetite: form.risk_appetite,
      target_retirement_corpus: Number(form.target_retirement_corpus),
      repatriation_intent: form.repatriation_intent,
      has_trc_form10f: form.has_trc_form10f,
    };

    try {
      const response = await fetch(`${API_URL}/generate-plan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(data?.error || `Request failed with status ${response.status}`);
      }

      setStatus("success");
      onGenerated?.(payload, data);
    } catch (err) {
      setStatus("error");
      setErrorMessage(
        err instanceof TypeError
          ? "Could not reach the Zaelor server. Is the backend running?"
          : err.message
      );
    }
  }

  function handleFormSubmit(e) {
    e.preventDefault();
    if (status === "loading") return;
    if (isLastStep) {
      submitPlan();
    } else {
      goNext();
    }
  }

  const visibleStack = [];
  for (let offset = 0; offset <= 2; offset++) {
    const idx = currentStep + offset;
    if (idx < STEPS.length) visibleStack.push({ s: STEPS[idx], index: idx, offset });
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-4xl mx-auto px-6 py-16 sm:py-24">
        <header className="mb-16 text-center">
          <div className="relative inline-block">
            <div
              aria-hidden="true"
              className="gold-underglow pointer-events-none absolute -inset-12 -z-10"
            />
            <motion.h1
              className="text-5xl sm:text-6xl font-extrabold tracking-tight text-text"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, ease: EASE_OUT }}
            >
              ZAELOR
            </motion.h1>
          </div>
          <p className="mt-3 text-secondary">Wealth beyond borders.</p>

          <div className="mt-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-card px-4 py-1.5 text-xs text-secondary">
            <ShieldCheck size={14} className="text-gold" />
            100% Anonymous &middot; No login &middot; No personal data
          </div>
        </header>

        <form onSubmit={handleFormSubmit}>
          <div className="relative h-[600px] sm:h-[540px]">
            <AnimatePresence>
              {visibleStack.map(({ s, index, offset }) => (
                <motion.div
                  key={s.id}
                  initial={cardEnter(offset, direction)}
                  animate={cardRest(offset)}
                  exit={cardLeave(direction)}
                  transition={TRANSITION}
                  style={{ zIndex: cardRest(offset).zIndex }}
                  className={`absolute inset-0 rounded-2xl border px-8 sm:px-10 py-10 overflow-hidden ${
                    offset === 0
                      ? "border-gold/25 bg-card shadow-[0_20px_60px_rgba(0,0,0,0.45)]"
                      : "border-white/10 bg-card pointer-events-none select-none"
                  }`}
                >
                  <p className="text-xs uppercase tracking-[0.15em] text-gold mb-1">
                    Step {index + 1} of {STEPS.length}
                  </p>
                  <h2 className="text-lg font-semibold text-text mb-6 tracking-tight">{s.title}</h2>
                  {offset === 0 && <StepFields stepId={s.id} form={form} update={update} />}
                </motion.div>
              ))}
            </AnimatePresence>
          </div>

          <StepDots total={STEPS.length} current={currentStep} />

          {status === "error" && (
            <div className="mt-6 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
              {errorMessage}
            </div>
          )}

          <div className="mt-8 flex items-center gap-4">
            <button
              type="button"
              onClick={goBack}
              disabled={currentStep === 0}
              className="flex-1 rounded-lg border border-white/10 bg-card text-secondary font-medium py-4 transition-opacity disabled:opacity-30 disabled:cursor-not-allowed hover:border-white/20 hover:text-text"
            >
              Back
            </button>
            <button
              type="submit"
              disabled={!canAdvance || status === "loading"}
              className="flex-[2] flex items-center justify-center gap-2 rounded-lg bg-gold text-black font-semibold py-4 transition-opacity disabled:opacity-40 disabled:cursor-not-allowed hover:opacity-90"
            >
              {status === "loading" ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Generating your wealth plan…
                </>
              ) : isLastStep ? (
                "Build My Wealth Plan"
              ) : (
                "Next"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
