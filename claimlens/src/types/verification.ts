
export type Verdict =
  | "supported"
  | "contradicted"
  | "misleading"
  | "mixed"
  | "unverified"
  | "not_fact_checkable";

export type EvidenceRelation =
  | "supports"
  | "contradicts"
  | "context";

export interface Evidence {
  id: string;
  title: string;
  domain: string;
  url: string;
  excerpt: string;
  relation: EvidenceRelation;
  publishedAt?: string;
  retrievedAt?: string;
  sourceType: string;
  limitations?: string;
}

export interface ClaimResult {
  id: string;
  text: string;
  verdict: Verdict;
  explanation: string;
  confidence: number | null;
  limitations: string[];
  evidence: Evidence[];
}

export interface VerificationReport {
  id: string;
  status: "demo" | "processing" | "completed" | "failed";
  createdAt: string;
  claims: ClaimResult[];
  auditTrail: {
    id: string;
    timestamp: string;
    event: string;
    details: string;
  }[];
}
