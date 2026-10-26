
import { useState } from "react";
import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import HomePage from "./routes/HomePage";
import AnalysisPage from "./routes/AnalysisPage";
import ReportPage from "./routes/ReportPage";
import { mockReport } from "./data/mockReport";
import { verifyClaim } from "./services/api";
import type { VerificationReport } from "./types/verification";

function AppRoutes() {
  const [claim, setClaim] = useState("");
  const [report, setReport] = useState<VerificationReport | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleVerify = async (submittedClaim: string) => {
    setClaim(submittedClaim);
    setError("");
    setReport(null);
    setIsLoading(true);
    navigate("/analysis");

    try {
      const result = await verifyClaim(submittedClaim);
      setReport(result);
      navigate("/report");
    } catch {
      setError(
        "We couldn't connect to the verification service. Please check whether the backend is running."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Routes>
      <Route
        path="/"
        element={<HomePage onVerify={handleVerify} />}
      />

      <Route
        path="/analysis"
        element={
          <AnalysisPage
            claim={claim}
            isLoading={isLoading}
            error={error}
          />
        }
      />

      <Route
        path="/report"
        element={
          <ReportPage report={report ?? mockReport} />
        }
      />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}

export default App;
