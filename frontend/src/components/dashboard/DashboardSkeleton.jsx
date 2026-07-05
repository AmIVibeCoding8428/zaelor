function Block({ className = "" }) {
  return <div className={`animate-pulse rounded-3xl bg-white/[0.04] ${className}`} />;
}

// Mirrors the real dashboard's layout so the fade-into-content swap never
// causes a height/scroll jump — every block matches its real counterpart's
// approximate footprint.
export default function DashboardSkeleton() {
  return (
    <div>
      <div className="mb-14">
        <Block className="h-64 mb-6" />
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
          <Block className="h-28 rounded-2xl" />
          <Block className="h-28 rounded-2xl" />
          <Block className="h-28 rounded-2xl" />
        </div>
      </div>

      <Block className="h-[560px] mb-14" />

      <div className="mb-12 grid grid-cols-2 sm:grid-cols-4 gap-6">
        <Block className="h-16 rounded-2xl" />
        <Block className="h-16 rounded-2xl" />
        <Block className="h-16 rounded-2xl" />
        <Block className="h-16 rounded-2xl" />
      </div>

      <div className="mb-12 space-y-6">
        <Block className="h-40" />
        <Block className="h-96" />
      </div>

      <Block className="h-80 mb-12" />
    </div>
  );
}
