import { useState } from "react";
import { Download, Loader2 } from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL;
const FALLBACK_FILENAME = "Zaelor-Wealth-Plan.pdf";

function filenameFromContentDisposition(header) {
  if (!header) return FALLBACK_FILENAME;
  const match = header.match(/filename="?([^";]+)"?/i);
  return match ? match[1] : FALLBACK_FILENAME;
}

export default function ReportDownloadButton({ plan, userInput }) {
  const [status, setStatus] = useState("idle"); // idle | loading | error
  const [errorMessage, setErrorMessage] = useState("");

  async function handleDownload() {
    if (status === "loading") return;
    setStatus("loading");
    setErrorMessage("");

    try {
      const response = await fetch(`${API_URL}/generate-report`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_input: userInput, plan }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new Error(data?.error || `Request failed with status ${response.status}`);
      }

      const blob = await response.blob();
      const filename = filenameFromContentDisposition(response.headers.get("Content-Disposition"));

      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);

      setStatus("idle");
    } catch (err) {
      setStatus("error");
      setErrorMessage(
        err instanceof TypeError ? "Could not reach the Zaelor server. Is the backend running?" : err.message
      );
    }
  }

  const isLoading = status === "loading";

  return (
    <div className="flex flex-col items-end gap-2">
      <button
        onClick={handleDownload}
        disabled={isLoading}
        className="group inline-flex items-center gap-2 rounded-full border border-gold/40 px-4 py-2 text-xs font-semibold text-gold transition-all duration-300 ease-out hover:bg-gold hover:text-black disabled:opacity-60 disabled:cursor-not-allowed"
      >
        {isLoading ? (
          <>
            <Loader2 size={13} className="animate-spin" />
            Generating&hellip;
          </>
        ) : (
          <>
            <Download size={13} className="transition-transform duration-300 ease-out group-hover:translate-y-0.5" />
            Download Report
          </>
        )}
      </button>
      {status === "error" && <p className="text-xs text-gold/80 max-w-xs text-right">{errorMessage}</p>}
    </div>
  );
}
