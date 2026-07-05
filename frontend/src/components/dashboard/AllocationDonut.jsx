import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";

// Gold reserved as the sole accent; everything else is warm-gray/slate/soft-white
// so segments read as refined tonal steps rather than competing accent colors.
const SLICE_COLORS = ["#C9A34E", "#E8E4DA", "#9A9284", "#6B7280", "#4B4B4B", "#5C5648"];

export default function AllocationDonut({ assetAllocation }) {
  const allocations = assetAllocation?.allocations ?? {};
  // Sorted largest-first so the gold accent always lands on the dominant
  // allocation rather than whatever key happens to sort first alphabetically.
  const data = Object.entries(allocations)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);

  const top = data[0];

  return (
    <section id="asset-allocation" className="scroll-mt-8 h-full">
      <div className="group rounded-3xl border border-white/[0.06] bg-card px-7 sm:px-10 py-9 sm:py-11 h-full transition-all duration-500 ease-out hover:border-gold/15">
        <h2 className="text-xs uppercase tracking-[0.18em] text-gold mb-3">Asset Allocation</h2>
        <h3 className="text-xl font-semibold text-text mb-8 tracking-tight">Recommended Portfolio Split</h3>

        <div className="flex flex-col sm:flex-row items-center gap-10">
          <div className="relative w-full sm:w-1/2 shrink-0">
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={data}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={78}
                  outerRadius={112}
                  startAngle={90}
                  endAngle={-270}
                  paddingAngle={3}
                  cornerRadius={4}
                  stroke="#0F0F0F"
                  strokeWidth={2}
                  isAnimationActive
                  animationDuration={900}
                  animationEasing="ease-out"
                >
                  {data.map((entry, index) => (
                    <Cell key={entry.name} fill={SLICE_COLORS[index % SLICE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: "#080808",
                    border: "1px solid rgba(201,163,78,0.18)",
                    borderRadius: 10,
                    color: "#FFFFFF",
                  }}
                  formatter={(value, name) => [`${value}%`, name]}
                />
              </PieChart>
            </ResponsiveContainer>

            {top && (
              <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                <p className="text-3xl font-bold tracking-tight text-gold">{top.value}%</p>
                <p className="mt-1 max-w-[7rem] text-center text-[11px] leading-snug text-secondary">{top.name}</p>
              </div>
            )}
          </div>

          <ul className="w-full sm:w-1/2 space-y-4">
            {data.map((entry, index) => (
              <li key={entry.name} className="flex items-center justify-between gap-3 text-sm">
                <span className="flex items-center gap-2.5 text-secondary min-w-0">
                  <span
                    className="w-2.5 h-2.5 rounded-full shrink-0"
                    style={{ backgroundColor: SLICE_COLORS[index % SLICE_COLORS.length] }}
                  />
                  <span className="truncate">{entry.name}</span>
                </span>
                <span className={`shrink-0 tabular-nums font-semibold ${index === 0 ? "text-gold" : "text-text"}`}>
                  {entry.value}%
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
