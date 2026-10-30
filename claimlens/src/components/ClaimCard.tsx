
import type { ClaimResult } from "../types/verification";
import VerdictBadge from "./VerdictBadge";
import EvidenceCard from "./EvidenceCard";

interface ClaimCardProps {
  claim: ClaimResult;
}

function ClaimCard({ claim }: ClaimCardProps) {
  return (
    <article className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 bg-slate-50 px-6 py-5 sm:px-8">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Analysis result
          </span>

          <VerdictBadge verdict={claim.verdict} />
        </div>

        <h3 className="mt-4 text-lg font-semibold leading-7 text-slate-900">
          {claim.text}
        </h3>
      </div>

      <div className="space-y-6 p-6 sm:p-8">
        <section>
          <h4 className="text-sm font-semibold text-slate-900">
            What does this result mean?
          </h4>

          <p className="mt-2 text-sm leading-6 text-slate-600">
            {claim.explanation}
          </p>
        </section>

        {claim.confidence !== null && (
          <section>
            <div className="flex items-center justify-between gap-3">
              <h4 className="text-sm font-semibold text-slate-900">
                Confidence
              </h4>

              <span className="text-sm font-semibold text-slate-700">
                {claim.confidence}%
              </span>
            </div>

            <div
              className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100"
              role="progressbar"
              aria-label="Confidence"
              aria-valuenow={claim.confidence}
              aria-valuemin={0}
              aria-valuemax={100}
            >
              <div
                className="h-full rounded-full bg-blue-600"
                style={{
                  width: `${Math.min(
                    100,
                    Math.max(0, claim.confidence)
                  )}%`,
                }}
              />
            </div>
          </section>
        )}

        {claim.limitations.length > 0 && (
          <section className="rounded-xl border border-amber-200 bg-amber-50 p-4">
            <h4 className="text-sm font-semibold text-amber-900">
              Important limitations
            </h4>

            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-6 text-amber-900">
              {claim.limitations.map((limitation, index) => (
                <li key={index}>{limitation}</li>
              ))}
            </ul>
          </section>
        )}

        <section>
          <div className="flex items-center justify-between gap-3">
            <h4 className="text-sm font-semibold text-slate-900">
              Evidence
            </h4>

            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
              {claim.evidence.length} sources
            </span>
          </div>

          {claim.evidence.length > 0 ? (
            <div className="mt-4 space-y-3">
              {claim.evidence.map((evidence) => (
                <EvidenceCard key={evidence.id} evidence={evidence} />
              ))}
            </div>
          ) : (
            <div className="mt-3 rounded-xl border border-dashed border-slate-300 px-4 py-6 text-center">
              <p className="text-sm font-medium text-slate-700">
                No evidence available yet
              </p>

              <p className="mt-1 text-xs leading-5 text-slate-500">
                Evidence sources will appear here when the verification
                backend is connected and returns them.
              </p>
            </div>
          )}
        </section>
      </div>
    </article>
  );
}

export default ClaimCard;
