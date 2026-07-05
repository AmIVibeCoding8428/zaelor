import { CheckCircle2, Circle } from "lucide-react";

export default function TaxAccountsSection({ taxAndAccounts }) {
  const accounts = taxAndAccounts?.recommended_accounts ?? [];

  return (
    <section id="tax-fema" className="mb-12 scroll-mt-8">
      <h2 className="text-xs uppercase tracking-[0.18em] text-gold mb-3">Tax & FEMA</h2>
      <h3 className="text-xl font-semibold text-text mb-6 tracking-tight">Recommended Account Structure</h3>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        {accounts.map((account) => (
          <div
            key={account.account_type}
            className="group rounded-3xl border border-white/[0.06] bg-card px-7 py-7 transition-all duration-500 ease-out hover:-translate-y-0.5 hover:border-gold/15"
          >
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-base font-semibold text-text">{account.account_type}</h4>
              {account.recommended ? (
                <CheckCircle2 size={16} className="text-gold" />
              ) : (
                <Circle size={16} className="text-secondary/50" />
              )}
            </div>
            <p className="text-xs text-secondary mb-4">{account.full_name}</p>

            <dl className="space-y-2 text-xs mb-4">
              <div className="flex justify-between gap-3">
                <dt className="text-secondary">Interest tax</dt>
                <dd className="text-text text-right">{account.interest_tax}</dd>
              </div>
              <div className="flex justify-between gap-3">
                <dt className="text-secondary">Repatriation</dt>
                <dd className="text-text text-right">{account.repatriation}</dd>
              </div>
            </dl>

            <p className="text-xs text-secondary leading-relaxed">{account.reason}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
