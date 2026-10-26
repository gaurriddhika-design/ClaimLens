
import type { VerificationReport } from "../types/verification";

interface ReportPageProps {
  report: VerificationReport;
}

function ReportPage({ report }: ReportPageProps) {
  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <h1 className="text-3xl font-bold text-slate-900">
        Verification Report
      </h1>

      {report.status === "demo" && (
  <p className="mt-2 text-sm font-semibold text-amber-700">
    DEMO DATA — NOT A LIVE VERIFICATION
  </p>
)}

      <p className="mt-2 text-sm text-slate-600">
        Review the findings and evidence recorded for this submission.
      </p>

      <section className="mt-6 rounded-xl border border-slate-200 bg-white p-6">
        <p className="text-sm text-slate-500">Report ID</p>
        <p className="mt-1 font-medium text-slate-900">{report.id}</p>

        <p className="mt-4 text-sm text-slate-500">Report status</p>
        <p className="mt-1 font-semibold capitalize text-slate-900">
          {report.status}
        </p>

        <p className="mt-4 text-sm text-slate-500">Claims in this report</p>
        <p className="mt-1 font-semibold text-slate-900">
          {report.claims.length}
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-bold text-slate-900">Claims & Findings</h2>

        {report.claims.length === 0 ? (
          <p className="mt-3 text-sm text-slate-600">
            No claims are available in this report.
          </p>
        ) : (
          <div className="mt-4 space-y-5">
            {report.claims.map((claim) => (
              <article
                key={claim.id}
                className="rounded-xl border border-slate-200 bg-white p-5"
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <span className="rounded-full bg-blue-50 px-3 py-1 text-sm font-semibold capitalize text-blue-800">
                    {claim.verdict.replaceAll("_", " ")}
                  </span>

                  {claim.confidence !== null && (
                    <span className="text-sm font-medium text-slate-600">
                      Confidence: {claim.confidence}%
                    </span>
                  )}
                </div>

                <h3 className="mt-4 font-semibold text-slate-900">
                  {claim.text}
                </h3>

                <h4 className="mt-4 text-sm font-semibold text-slate-800">
                  Explanation
                </h4>
                <p className="mt-1 text-sm leading-6 text-slate-600">
                  {claim.explanation}
                </p>

                <div className="mt-5">
                  <h4 className="font-semibold text-slate-900">
                    Evidence Sources ({claim.evidence.length})
                  </h4>

                  {claim.evidence.length === 0 ? (
                    <p className="mt-2 text-sm text-slate-500">
                      No evidence sources are available.
                    </p>
                  ) : (
                    <div className="mt-3 space-y-3">
                      {claim.evidence.map((item) => (
                        <div
                          key={item.id}
                          className="rounded-lg border border-slate-200 p-4"
                        >
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <span className="font-medium text-slate-900">
                              {item.title}
                            </span>

                            <span
                              className={`rounded-full px-2 py-1 text-xs font-semibold ${
                                item.relation === "supports"
                                  ? "bg-green-50 text-green-700"
                                  : item.relation === "contradicts"
                                    ? "bg-red-50 text-red-700"
                                    : "bg-amber-50 text-amber-700"
                              }`}
                            >
                              {item.relation === "supports"
                                ? "Supports claim"
                                : item.relation === "contradicts"
                                  ? "Contradicts claim"
                                  : "Context"}
                            </span>
                          </div>

                          <p className="mt-1 text-xs text-slate-500">
                            {item.domain} · {item.sourceType}
                          </p>

                          <p className="mt-2 text-sm leading-6 text-slate-600">
                            {item.excerpt}
                          </p>

                          {item.publishedAt && (
                            <p className="mt-2 text-xs text-slate-500">
                              Published: {item.publishedAt}
                            </p>
                          )}

                          {item.limitations && (
                            <p className="mt-2 text-sm text-amber-800">
                              Limitation: {item.limitations}
                            </p>
                          )}

                          <a
                            href={item.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="mt-3 inline-block text-sm font-semibold text-blue-700 underline hover:text-blue-900"
                          >
                            Read source →
                          </a>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {claim.limitations.length > 0 && (
                  <div className="mt-5 rounded-lg bg-amber-50 p-4">
                    <h4 className="font-semibold text-amber-900">
                      Verification Limitations
                    </h4>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-amber-800">
                      {claim.limitations.map((limitation, index) => (
                        <li key={`${claim.id}-limitation-${index}`}>
                          {limitation}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </article>
            ))}
          </div>
        )}
      </section>

      <p className="mt-8 text-xs leading-5 text-slate-500">
        Review the original sources and limitations before relying on a verdict.
        Confidence scores are estimates, not guarantees of truth.
      </p>
    </main>
  );
}

export default ReportPage;
