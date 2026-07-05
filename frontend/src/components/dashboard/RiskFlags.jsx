import { AlertTriangle } from "lucide-react";

export default function RiskFlags({ riskFlags }) {
  if (!riskFlags || riskFlags.length === 0) return null;

  return (
    <section className="mb-12">
      <h2 className="text-xs uppercase tracking-[0.18em] text-gold mb-4">Risk Flags</h2>
      <div className="space-y-3">
        {riskFlags.map((flag) => (
          <div
            key={flag.code}
            className="flex items-start gap-3 rounded-2xl border border-gold/15 bg-gold/[0.03] px-6 py-4 transition-colors duration-500 ease-out hover:border-gold/25"
          >
            <AlertTriangle size={16} className="text-gold shrink-0 mt-0.5" />
            <p className="text-sm text-secondary leading-relaxed">{flag.message}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
