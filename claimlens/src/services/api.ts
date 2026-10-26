
import type { VerificationReport } from "../types/verification";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function verifyClaim(
  claim: string
): Promise<VerificationReport> {
  const response = await fetch(`${API_BASE_URL}/verify`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ claim }),
  });

  if (!response.ok) {
    throw new Error(
      `Verification failed: ${response.status} ${response.statusText}`
    );
  }

  return (await response.json()) as VerificationReport;
}
