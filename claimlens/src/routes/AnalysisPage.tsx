
import { useNavigate } from "react-router-dom";
import FileUploader from "../components/FileUploader";
import AnalysisProgress from "../components/AnalysisProgress";
import SourcePanel from "../components/SourcePanel";
import AuditTimeline from "../components/AuditTimeline";

interface AnalysisPageProps {
  claim: string;
  isLoading: boolean;
  error: string;
}

function AnalysisPage({
  claim,
  isLoading,
  error,
}: AnalysisPageProps) {
  const navigate = useNavigate();

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <h1 className="text-2xl font-bold text-slate-900">
        Analyzing your claim
      </h1>

      <p className="mt-3 text-sm text-slate-600">
        ClaimLens is preparing the claim for verification.
      </p>

      <div className="mt-6 rounded-xl border border-slate-200 bg-white p-5">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Submitted claim
        </p>

        <p className="mt-2 text-slate-800">{claim}</p>

        {isLoading && (
          <p className="mt-4 text-sm text-blue-700">
            Verification is in progress. Please wait...
          </p>
        )}

        {error && (
          <p role="alert" className="mt-4 text-sm text-red-700">
            {error}
          </p>
        )}
      </div>

      <FileUploader
        onFileSelect={(file) =>
          console.log("Selected file:", file.name)
        }
      />

      <AnalysisProgress
        progress={isLoading ? 50 : error ? 0 : 100}
        message={
          isLoading
            ? "Verification in progress..."
            : error
              ? "Verification failed"
              : "Verification request completed"
        }
      />

      <SourcePanel sources={[]} />

      <AuditTimeline
        events={[
          {
            title: "Claim submitted",
            description: "Your claim has been received.",
          },
          {
            title: "Verification status",
            description: isLoading
              ? "Verification is in progress."
              : error
                ? "Verification encountered an error."
                : "The verification request has finished.",
          },
        ]}
      />

      <button
        type="button"
        onClick={() => navigate("/report")}
        className="mt-6 rounded-xl bg-blue-700 px-5 py-3 font-semibold text-white hover:bg-blue-800"
      >
        View Report →
      </button>
    </main>
  );
}

export default AnalysisPage;
