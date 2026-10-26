
import type { Evidence } from "../types/verification";

interface EvidenceCardProps {
  evidence: Evidence;
}

function EvidenceCard({ evidence }: EvidenceCardProps) {
  const relationStyles = {
    supports: "bg-green-100 text-green-800",
    contradicts: "bg-red-100 text-red-800",
    context: "bg-blue-100 text-blue-800",
  };

  const relationLabels = {
    supports: "Supports claim",
    contradicts: "Contradicts claim",
    context: "Provides context",
  };

  return (
    <article className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h3 className="font-semibold text-slate-900">
          {evidence.title}
        </h3>

        <span
          className={`rounded-full px-3 py-1 text-xs font-medium ${relationStyles[evidence.relation]}`}
        >
          {relationLabels[evidence.relation]}
        </span>
      </div>

      <p className="mt-2 text-sm text-slate-500">
        Source: {evidence.domain}
      </p>

      <p className="mt-3 text-slate-700">
        {evidence.excerpt}
      </p>

      {evidence.publishedAt && (
        <p className="mt-2 text-xs text-slate-500">
          Published: {evidence.publishedAt}
        </p>
      )}

      {evidence.limitations && (
        <p className="mt-3 text-sm text-amber-700">
          Limitation: {evidence.limitations}
        </p>
      )}

      <a
        href={evidence.url}
        target="_blank"
        rel="noreferrer"
        className="mt-4 inline-block text-sm font-medium text-blue-600 underline"
      >
        Open source
      </a>
    </article>
  );
}

export default EvidenceCard;
