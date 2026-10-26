import { useNavigate } from "react-router-dom";
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
