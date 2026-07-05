import { renderMarkdownLite } from "../../lib/markdownLite";
import ReportDownloadButton from "./ReportDownloadButton";

export default function MemoSection({ memo, plan, userInput }) {
  return (
    <section id="reports" className="mb-12 scroll-mt-8">
      <div className="flex items-start justify-between gap-6 mb-7">
        <div>
          <h2 className="text-xs uppercase tracking-[0.18em] text-gold mb-3">Reports</h2>
          <h3 className="text-xl font-semibold text-text tracking-tight">Advisory Summary</h3>
        </div>
        <ReportDownloadButton plan={plan} userInput={userInput} />
      </div>

      <div className="group rounded-3xl border border-white/[0.06] bg-card px-6 sm:px-12 py-10 transition-all duration-500 ease-out hover:border-gold/15">
        {renderMarkdownLite(memo)}
      </div>
    </section>
  );
}
