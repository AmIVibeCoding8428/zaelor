import {
  LayoutDashboard,
  UserRound,
  PieChart,
  Calculator,
  TrendingUp,
  Landmark,
  FileText,
  ShieldCheck,
  RotateCcw,
} from "lucide-react";

const NAV_ITEMS = [
  { href: "#hero", label: "Dashboard", icon: LayoutDashboard },
  { href: "#profile-summary", label: "Profile Summary", icon: UserRound },
  { href: "#asset-allocation", label: "Asset Allocation", icon: PieChart },
  { href: "#sip-planner", label: "SIP Planner", icon: Calculator },
  { href: "#monte-carlo", label: "Monte Carlo Analysis", icon: TrendingUp },
  { href: "#tax-fema", label: "Tax & FEMA", icon: Landmark },
  { href: "#reports", label: "Reports", icon: FileText },
];

export default function Sidebar({ onReset }) {
  return (
    <aside className="hidden lg:flex lg:flex-col w-64 shrink-0 border-r border-white/[0.06] bg-background px-5 py-8 h-screen sticky top-0">
      <div className="mb-10 px-2">
        <h1 className="text-lg font-bold tracking-wide text-text">
          ZAELOR
          <span className="ml-1.5 inline-block h-1.5 w-1.5 rounded-full bg-gold align-middle" />
        </h1>
        <p className="text-xs text-secondary mt-1.5">Wealth beyond borders.</p>
      </div>

      <nav className="flex-1 space-y-1">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => (
          <a
            key={href}
            href={href}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-secondary hover:text-text hover:bg-white/5 transition-colors"
          >
            <Icon size={16} className="shrink-0" />
            {label}
          </a>
        ))}
      </nav>

      <div className="space-y-3 px-1">
        <button
          onClick={onReset}
          className="flex items-center gap-2 px-2 py-2 text-xs text-secondary hover:text-gold transition-colors"
        >
          <RotateCcw size={13} />
          Start a new plan
        </button>

        <div className="flex items-start gap-2 rounded-lg border border-white/10 bg-card px-3 py-3 text-xs text-secondary">
          <ShieldCheck size={15} className="text-gold shrink-0 mt-0.5" />
          <span>100% Anonymous</span>
        </div>
      </div>
    </aside>
  );
}
