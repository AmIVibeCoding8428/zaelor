import { useRef } from "react";
import { useInView } from "motion/react";
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import { formatCompactINR } from "../../lib/format";

// Custom content: the Area series shares the "Median" dataKey purely to
// render the gradient fill under the gold line, so recharts' default
// Tooltip would otherwise list "Median" twice (once for the area, once for
// the line). Filter to one row per dataKey, keeping the real (named) line.
function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const seen = new Set();
  const rows = payload.filter((entry) => {
    if (entry.name.startsWith("_") || seen.has(entry.dataKey)) return false;
    seen.add(entry.dataKey);
    return true;
  });

  return (
    <div
      style={{
        background: "#0F0F0F",
        border: "1px solid rgba(201,163,78,0.18)",
        borderRadius: 10,
        boxShadow: "0 16px 48px rgba(0,0,0,0.55)",
        padding: "12px 16px",
      }}
    >
      <p style={{ color: "#9A9A9A", fontSize: 12, margin: "0 0 8px", letterSpacing: "0.04em" }}>
        {`YEAR ${label}`}
      </p>
      {rows.map((entry) => (
        <p key={entry.dataKey} style={{ color: "#FFFFFF", fontSize: 13, margin: "3px 0", fontWeight: entry.dataKey === "Median" ? 600 : 400 }}>
          <span style={{ color: entry.color }}>{entry.name}</span>: {formatCompactINR(entry.value)}
        </p>
      ))}
    </div>
  );
}

// Legend built by hand (rather than recharts' default) so Median — the line
// that actually answers "what will I have" — reads as the primary series,
// with Best/Worst demoted to dashed, muted context lines.
function ChartLegend() {
  return (
    <div className="flex items-center gap-6 text-xs">
      <span className="flex items-center gap-2 text-text font-medium">
        <span className="h-2 w-2 rounded-full bg-gold" />
        Median
      </span>
      <span className="flex items-center gap-2 text-secondary">
        <span className="h-px w-3.5 bg-white/45" />
        Best Case
      </span>
      <span className="flex items-center gap-2 text-secondary">
        <span className="h-px w-3.5 bg-secondary/60" />
        Worst Case
      </span>
    </div>
  );
}

export default function NetWorthChart({ monteCarlo }) {
  const median = monteCarlo?.median_case ?? [];
  const best = monteCarlo?.best_case ?? [];
  const worst = monteCarlo?.worst_case ?? [];

  const data = median.map((value, index) => ({
    year: index + 1,
    Median: value,
    Best: best[index],
    Worst: worst[index],
  }));

  const containerRef = useRef(null);
  const isInView = useInView(containerRef, { once: true, amount: 0.35 });

  return (
    <section id="monte-carlo" className="mb-14 scroll-mt-8">
      <div className="group rounded-3xl border border-white/[0.06] bg-card px-6 sm:px-14 py-12 sm:py-16 transition-all duration-500 ease-out hover:border-gold/15">
        <div className="mb-10 flex flex-col sm:flex-row sm:items-end sm:justify-between gap-6">
          <div>
            <h2 className="text-xs uppercase tracking-[0.18em] text-gold mb-3">Monte Carlo Analysis</h2>
            <h3 className="text-3xl font-semibold text-text tracking-tight">
              Projected Net Worth Over {median.length} Years
            </h3>
            <p className="text-xs text-secondary mt-2.5">
              Based on {monteCarlo?.num_simulations?.toLocaleString() ?? "10,000"} simulated market
              scenarios.
            </p>
          </div>
          <ChartLegend />
        </div>

        <div ref={containerRef} style={{ height: 460 }}>
          {isInView && (
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 8 }}>
                <defs>
                  <linearGradient id="medianFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#C9A34E" stopOpacity={0.28} />
                    <stop offset="100%" stopColor="#C9A34E" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="2 6" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis
                  dataKey="year"
                  stroke="#9A9A9A"
                  tick={{ fill: "#9A9A9A", fontSize: 12 }}
                  tickLine={false}
                  axisLine={{ stroke: "rgba(255,255,255,0.08)" }}
                  label={{ value: "Years to Retirement", position: "insideBottom", offset: -4, fill: "#9A9A9A", fontSize: 12 }}
                />
                <YAxis
                  stroke="#9A9A9A"
                  tick={{ fill: "#9A9A9A", fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value) => formatCompactINR(value)}
                  width={84}
                />
                <Tooltip
                  content={<ChartTooltip />}
                  cursor={{ stroke: "rgba(201,163,78,0.35)", strokeWidth: 1, strokeDasharray: "3 5" }}
                />
                <Area
                  type="monotone"
                  dataKey="Median"
                  name="_medianFill"
                  stroke="none"
                  fill="url(#medianFill)"
                  isAnimationActive
                  animationDuration={1400}
                  animationEasing="ease-out"
                  legendType="none"
                />
                <Line
                  type="monotone"
                  dataKey="Best"
                  stroke="#FFFFFF"
                  strokeWidth={1.5}
                  strokeOpacity={0.4}
                  strokeDasharray="4 4"
                  dot={false}
                  activeDot={{ r: 4, fill: "#FFFFFF", stroke: "#0F0F0F", strokeWidth: 2 }}
                  isAnimationActive
                  animationDuration={1400}
                  animationEasing="ease-out"
                />
                <Line
                  type="monotone"
                  dataKey="Median"
                  stroke="#C9A34E"
                  strokeWidth={3}
                  dot={false}
                  activeDot={{ r: 5, fill: "#C9A34E", stroke: "#0F0F0F", strokeWidth: 2 }}
                  isAnimationActive
                  animationDuration={1400}
                  animationEasing="ease-out"
                />
                <Line
                  type="monotone"
                  dataKey="Worst"
                  stroke="#9A9A9A"
                  strokeWidth={1.5}
                  strokeOpacity={0.5}
                  strokeDasharray="4 4"
                  dot={false}
                  activeDot={{ r: 4, fill: "#9A9A9A", stroke: "#0F0F0F", strokeWidth: 2 }}
                  isAnimationActive
                  animationDuration={1400}
                  animationEasing="ease-out"
                />
              </ComposedChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </section>
  );
}
