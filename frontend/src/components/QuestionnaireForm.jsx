import { useState } from "react";
import { Loader2, ShieldCheck } from "lucide-react";

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

function FieldLabel({ children, hint }) {
  return (
    <label className="block mb-2">
      <span className="text-sm font-medium text-text">{children}</span>
      {hint && <span className="block text-xs text-secondary mt-0.5">{hint}</span>}
    </label>
  );
}

function NumberField({ id, label, hint, value, onChange, placeholder, prefix }) {
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
          type="number"
          inputMode="decimal"
          required
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className={`w-full bg-card border border-white/10 rounded-lg py-3 ${
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
                : "border-white/10 bg-card text-secondary hover:border-white/20"
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function SectionHeading({ eyebrow, title }) {
  return (
    <div className="mb-6">
      <p className="text-xs uppercase tracking-wider text-gold mb-1">{eyebrow}</p>
      <h2 className="text-lg font-semibold text-text">{title}</h2>
    </div>
  );
}

export default function QuestionnaireForm() {
  const [form, setForm] = useState(INITIAL_FORM);
  const [status, setStatus] = useState("idle"); // idle | loading | success | error
  const [errorMessage, setErrorMessage] = useState("");

  const update = (field) => (value) => setForm((prev) => ({ ...prev, [field]: value }));

  const isComplete =
    form.age !== "" &&
    form.target_retirement_age !== "" &&
    form.monthly_income !== "" &&
    form.monthly_expenses !== "" &&
    form.monthly_feasible_investment_amount !== "" &&
    form.existing_indian_assets !== "" &&
    form.existing_foreign_assets !== "" &&
    form.target_retirement_corpus !== "" &&
    form.risk_appetite &&
    form.repatriation_intent !== null &&
    form.has_trc_form10f !== null;

  async function handleSubmit(e) {
    e.preventDefault();
    if (!isComplete || status === "loading") return;

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

      console.log("Wealth plan response:", data);
      setStatus("success");
    } catch (err) {
      setStatus("error");
      setErrorMessage(
        err instanceof TypeError
          ? "Could not reach the Zaelor server. Is the backend running?"
          : err.message
      );
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-3xl mx-auto px-6 py-16 sm:py-24">
        <header className="mb-14 text-center">
          <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight text-text">
            Zael<span className="text-gold">o</span>r
          </h1>
          <p className="mt-2 text-secondary">Wealth beyond borders.</p>

          <div className="mt-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-card px-4 py-1.5 text-xs text-secondary">
            <ShieldCheck size={14} className="text-gold" />
            100% Anonymous &middot; No login &middot; No personal data
          </div>
        </header>

        <form onSubmit={handleSubmit} className="space-y-12">
          <section>
            <SectionHeading eyebrow="Step 1" title="Profile & Timeline" />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <NumberField
                id="age"
                label="Current age"
                value={form.age}
                onChange={update("age")}
                placeholder="35"
              />
              <NumberField
                id="target_retirement_age"
                label="Target retirement age"
                value={form.target_retirement_age}
                onChange={update("target_retirement_age")}
                placeholder="60"
              />
            </div>
            <div className="mt-6">
              <FieldLabel hint="v1 scope is limited to UAE-based NRIs.">
                Country of residence
              </FieldLabel>
              <div className="w-full sm:w-1/2 bg-card border border-white/10 rounded-lg py-3 px-4 text-secondary">
                UAE
              </div>
            </div>
          </section>

          <section>
            <SectionHeading eyebrow="Step 2" title="Monthly Cash Flow" />
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
          </section>

          <section>
            <SectionHeading eyebrow="Step 3" title="Existing Assets" />
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
          </section>

          <section>
            <SectionHeading eyebrow="Step 4" title="Risk & Goals" />
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
                        : "border-white/10 bg-card text-secondary hover:border-white/20"
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
          </section>

          <section>
            <SectionHeading eyebrow="Step 5" title="Tax & Repatriation" />
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
          </section>

          {status === "error" && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
              {errorMessage}
            </div>
          )}

          <button
            type="submit"
            disabled={!isComplete || status === "loading"}
            className="w-full flex items-center justify-center gap-2 rounded-lg bg-gold text-black font-semibold py-4 transition-opacity disabled:opacity-40 disabled:cursor-not-allowed hover:opacity-90"
          >
            {status === "loading" ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                Generating your wealth plan…
              </>
            ) : (
              "Generate Wealth Plan"
            )}
          </button>

          {status === "success" && (
            <div className="rounded-lg border border-gold/30 bg-gold/10 px-4 py-3 text-sm text-gold text-center">
              Plan generated successfully — check the browser console for the full response.
            </div>
          )}
        </form>
      </div>
    </div>
  );
}
