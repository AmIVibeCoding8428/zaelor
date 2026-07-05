import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import Sidebar from "./dashboard/Sidebar";
import HeroKpis from "./dashboard/HeroKpis";
import ProfileSummary from "./dashboard/ProfileSummary";
import NetWorthChart from "./dashboard/NetWorthChart";
import AllocationDonut from "./dashboard/AllocationDonut";
import SipPlanSummary from "./dashboard/SipPlanSummary";
import RetirementAgeCard from "./dashboard/RetirementAgeCard";
import TaxAccountsSection from "./dashboard/TaxAccountsSection";
import MemoSection from "./dashboard/MemoSection";
import RiskFlags from "./dashboard/RiskFlags";
import DashboardSkeleton from "./dashboard/DashboardSkeleton";

const EASE_OUT = [0.16, 1, 0.3, 1];

export default function Dashboard({ plan, userInput, onReset }) {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setReady(true), 500);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="min-h-screen bg-background flex animate-[fadein_0.4s_ease-out]">
      <Sidebar onReset={onReset} />

      <main className="flex-1 pl-8 sm:pl-12 pr-8 sm:pr-14 py-12 sm:py-14 max-w-7xl">
        <AnimatePresence mode="wait">
          {!ready ? (
            <motion.div key="skeleton" exit={{ opacity: 0 }} transition={{ duration: 0.3, ease: EASE_OUT }}>
              <DashboardSkeleton />
            </motion.div>
          ) : (
            <motion.div
              key="content"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: EASE_OUT }}
            >
              <HeroKpis plan={plan} userInput={userInput} />
              <NetWorthChart monteCarlo={plan.monte_carlo} />
              <ProfileSummary userInput={userInput} yearsToRetirement={plan.asset_allocation?.years_to_retirement} />

              <section className="mb-12 scroll-mt-8">
                <h2 className="text-xs uppercase tracking-[0.18em] text-gold mb-4">Recommendations</h2>
                <div className="space-y-6">
                  <RetirementAgeCard recommendedRetirementAge={plan.recommended_retirement_age} />
                  <SipPlanSummary sipPlan={plan.sip_plan} monteCarlo={plan.monte_carlo} />
                </div>
              </section>

              <div className="mb-12">
                <AllocationDonut assetAllocation={plan.asset_allocation} />
              </div>

              <TaxAccountsSection taxAndAccounts={plan.tax_and_accounts} />
              <MemoSection memo={plan.memo} plan={plan} userInput={userInput} />
              <RiskFlags riskFlags={plan.tax_and_accounts?.risk_flags} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
