
import type { Verdict } from "../types/verification";

const verdictStyles: Record<Verdict, string> = {
  supported:
    "bg-emerald-500/10 text-emerald-300 border-emerald-500/30",
  contradicted:
    "bg-red-500/10 text-red-300 border-red-500/30",
  misleading:
    "bg-amber-500/10 text-amber-300 border-amber-500/30",
  mixed:
    "bg-purple-500/10 text-purple-300 border-purple-500/30",
  unverified:
    "bg-blue-500/10 text-blue-300 border-blue-500/30",
  not_fact_checkable:
    "bg-gray-500/10 text-gray-300 border-gray-500/30",
};

const verdictLabels: Record<Verdict, string> = {
  supported: "Supported",
  contradicted: "Contradicted",
  misleading: "Misleading / Missing Context",
  mixed: "Mixed Evidence",
  unverified: "Unverified",
  not_fact_checkable: "Not Fact-Checkable",
};

export default function VerdictBadge({
  verdict,
}: {
  verdict: Verdict;
}) {
  return (
    <span
      className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${verdictStyles[verdict]}`}
    >
      {verdictLabels[verdict]}
    </span>
  );
}
