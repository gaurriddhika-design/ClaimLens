
import type { VerificationReport } from "../types/verification";

export const mockReport: VerificationReport = {
  id: "demo-001",
  status: "demo",
  createdAt: "2026-10-26T10:00:00Z",

  claims: [
    {
      id: "claim-001",
      text: "The Earth revolves around the Sun.",
      verdict: "supported",
      explanation:
        "This is an established scientific fact. The example demonstrates how a supported claim appears in the dashboard.",
      confidence: 99,
      limitations: [
        "This is a demonstration result, not a live source-based verification.",
      ],
      evidence: [
        {
          id: "evidence-001",
          title: "Earth's Orbit Around the Sun",
          domain: "example.org",
          url: "https://example.org/",
          excerpt:
            "Illustrative evidence excerpt. Replace this with a verified passage from a real source when the backend is connected.",
          relation: "supports",
          sourceType: "Demo source",
          limitations: "Placeholder content; not a real citation.",
        },
      ],
    },
    {
      id: "claim-002",
      text: "Every online article is accurate.",
      verdict: "contradicted",
      explanation:
        "The word 'every' makes this a universal claim. Online articles can contain errors, unsupported statements, or misleading information.",
      confidence: null,
      limitations: [
        "This is an illustrative verdict, not a live verification.",
      ],
      evidence: [
        {
          id: "evidence-002",
          title: "Illustrative contradictory evidence",
          domain: "example.org",
          url: "https://example.org/",
          excerpt:
            "Placeholder evidence showing how a source card for contradictory evidence could appear.",
          relation: "contradicts",
          sourceType: "Demo source",
          limitations: "Placeholder content; not a real citation.",
        },
      ],
    },
  ],

  auditTrail: [
    {
      id: "audit-001",
      timestamp: "10:00:00",
      event: "Demo report loaded",
      details:
        "Sample data loaded locally; no external search was performed.",
    },
  ],
};
