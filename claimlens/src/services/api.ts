
import type { VerificationReport, Verdict, Evidence } from "../types/verification";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"
).replace(/\/+$/, "");

interface BackendEvidence {
  evidence_id: string;
  source_title: string;
  source_url: string | null;
  excerpt: string | null;
  source_type: string;
  supports_claim: boolean | null;
  retrieved_at: string | null;
}

interface BackendClaim {
  claim_id: string;
  original_text: string;
  verdict: string;
  explanation: string;
  confidence_level: string;
  supporting_evidence_ids: string[];
  contradicting_evidence_ids: string[];
  limitations: string[];
}

interface BackendReport {
  report_id: string;
  input_type: "text" | "url" | "pdf" | "demo";
  created_at: string;
  processing_status: "queued" | "processing" | "completed" | "failed";
  claims: BackendClaim[];
  evidence: BackendEvidence[];
  audit_events: {
    event_type: string;
    occurred_at: string;
    details: string;
  }[];
}

function mapVerdict(value: string): Verdict {
  const mapping: Record<string, Verdict> = {
    SUPPORTED: "supported",
    CONTRADICTED: "contradicted",
    MISLEADING_OR_MISSING_CONTEXT: "misleading",
    MIXED_EVIDENCE: "mixed",
    UNVERIFIED: "unverified",
    NOT_FACT_CHECKABLE: "not_fact_checkable",
  };

  return mapping[value] ?? "unverified";
}

function mapReport(data: BackendReport): VerificationReport {
  const evidenceById = new Map(
    data.evidence.map((item) => [item.evidence_id, item])
  );

  return {
    id: data.report_id,
    status:
      data.input_type === "demo"
        ? "demo"
        : data.processing_status === "queued"
          ? "processing"
          : data.processing_status,
    createdAt: data.created_at,
    claims: data.claims.map((claim) => {
      const supporting = new Set(claim.supporting_evidence_ids);
      const contradicting = new Set(claim.contradicting_evidence_ids);

      const relatedIds = [
        ...new Set([
          ...claim.supporting_evidence_ids,
          ...claim.contradicting_evidence_ids,
        ]),
      ];

      const mappedEvidence: Evidence[] = relatedIds.flatMap((id) => {
        const item = evidenceById.get(id);
        if (!item) return [];

        let relation: Evidence["relation"] = "context";
        if (supporting.has(id)) relation = "supports";
        else if (contradicting.has(id)) relation = "contradicts";

        let domain = "Unknown source";
        if (item.source_url) {
          try {
            domain = new URL(item.source_url).hostname;
          } catch {
            // Keep the fallback domain for invalid URLs.
          }
        }

        return [{
          id: item.evidence_id,
          title: item.source_title,
          domain,
          url: item.source_url || "",
          excerpt: item.excerpt || "No excerpt available.",
          relation,
          retrievedAt: item.retrieved_at || undefined,
          sourceType: item.source_type,
        }];
      });

      return {
        id: claim.claim_id,
        text: claim.original_text,
        verdict: mapVerdict(claim.verdict),
        explanation: claim.explanation,
        confidence: null,
        limitations: claim.limitations || [],
        evidence: mappedEvidence,
      };
    }),
    auditTrail: data.audit_events.map((event, index) => ({
      id: `${data.report_id}-event-${index}`,
      timestamp: event.occurred_at,
      event: event.event_type,
      details: event.details,
    })),
  };
}

export async function verifyClaim(
  claim: string
): Promise<VerificationReport> {
  const response = await fetch(`${API_BASE_URL}/api/verify`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text: claim }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    const message =
      typeof errorData?.detail === "string"
        ? errorData.detail
        : `Verification failed: ${response.status} ${response.statusText}`;

    throw new Error(message);
  }

  const data = (await response.json()) as BackendReport;
  return mapReport(data);
}
