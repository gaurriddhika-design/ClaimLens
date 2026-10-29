import { useState } from 'react'
import { FileText, Upload, ShieldCheck, LoaderCircle, AlertCircle, CheckCircle2, ExternalLink } from 'lucide-react'
import './App.css'

type Claim = {
  claim_id: string
  original_text: string
  source_location?: string | null
  verdict: string
  explanation: string
  confidence_level: string
}

type Evidence = {
  evidence_id: string
  source_title: string
  source_url?: string | null
  excerpt?: string | null
  source_type: string
  supports_claim?: boolean | null
}

type Report = {
  report_id: string
  input_type: string
  input_summary: string
  processing_status: string
  overall_summary: string
  total_claims: number
  verdict_counts: Record<string, number>
  claims: Claim[]
  evidence: Evidence[]
}

const API_URL = 'http://localhost:8000/api/verify/pdf'

function App() {
  const [file, setFile] = useState<File | null>(null)
  const [report, setReport] = useState<Report | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function verifyPDF() {
    if (!file) {
      setError('Please select a PDF file first.')
      return
    }

    setLoading(true)
    setError('')
    setReport(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(API_URL, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const data = await response.json().catch(() => null)
        throw new Error(
          data?.detail || `Verification failed (${response.status})`,
        )
      }

      const data: Report = await response.json()
      setReport(data)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Something went wrong. Please try again.',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="#">
          <span className="brand-icon"><ShieldCheck size={24} /></span>
          <span>ClaimLens</span>
        </a>
        <span className="topbar-label">AI-POWERED DOCUMENT VERIFICATION</span>
      </header>

      <section className="intro">
        <span className="eyebrow">DOCUMENT INTELLIGENCE</span>
        <h1>See beyond the <span>claim.</span></h1>
        <p>
          Upload a document to extract claims, review evidence, and understand
          what the available information supports.
        </p>
      </section>

      <section className="upload-card">
        <div className="section-heading">
          <span className="step-number">01</span>
          <div>
            <h2>Upload your document</h2>
            <p>Choose a PDF containing the information you want to verify.</p>
          </div>
        </div>

        <label className="dropzone">
          <input
            type="file"
            accept=".pdf,application/pdf"
            onChange={(event) => {
              setFile(event.target.files?.[0] ?? null)
              setReport(null)
              setError('')
            }}
          />
          <span className="upload-icon"><Upload size={25} /></span>
          <strong>{file ? file.name : 'Choose a PDF to get started'}</strong>
          <span className="file-hint">
            {file
              ? `${(file.size / (1024 * 1024)).toFixed(2)} MB`
              : 'Click to browse files · PDF format'}
          </span>
        </label>

        <button
          className="verify-button"
          onClick={verifyPDF}
          disabled={loading || !file}
        >
          {loading ? (
            <><LoaderCircle className="spin" size={19} /> Verifying document...</>
          ) : (
            <><ShieldCheck size={19} /> Verify document</>
          )}
        </button>

        {error && (
          <div className="error-message" role="alert">
            <AlertCircle size={19} />
            <span>{error}</span>
          </div>
        )}
      </section>

      {loading && (
        <p className="loading-note">
          Your document is being processed. This may take a little time.
        </p>
      )}

      {report && (
        <section className="results">
          <div className="results-heading">
            <div>
              <span className="eyebrow">VERIFICATION REPORT</span>
              <h2>Document results</h2>
            </div>
            <span className="status-pill">
              <CheckCircle2 size={16} /> {report.processing_status}
            </span>
          </div>

          <div className="summary-card">
            <span className="summary-label">OVERALL SUMMARY</span>
            <p>{report.overall_summary}</p>
            <div className="summary-footer">
              <FileText size={17} />
              {report.total_claims} claims identified
            </div>
          </div>

          <h3 className="subheading">Verdict breakdown</h3>
          <div className="verdict-grid">
            {Object.entries(report.verdict_counts).map(([verdict, count]) => (
              <div className="verdict-card" key={verdict}>
                <strong>{count}</strong>
                <span>{verdict.replaceAll('_', ' ')}</span>
              </div>
            ))}
          </div>

          <h3 className="subheading">Claims analysis</h3>
          {report.claims.map((claim) => (
            <article className="claim-card" key={claim.claim_id}>
              <div className="claim-topline">
                <span className="claim-id">{claim.claim_id}</span>
                <span className={`verdict-tag verdict-${claim.verdict.toLowerCase()}`}>
                  {claim.verdict.replaceAll('_', ' ')}
                </span>
              </div>
              <p className="claim-text">{claim.original_text}</p>
              <p className="claim-explanation">{claim.explanation}</p>
              <div className="confidence">
                Confidence: <strong>{claim.confidence_level.replaceAll('_', ' ')}</strong>
              </div>
              {claim.source_location && (
                <p className="source-location">
                  Location: {claim.source_location}
                </p>
              )}
            </article>
          ))}

          <h3 className="subheading">Evidence sources</h3>
          {report.evidence.length === 0 ? (
            <p className="empty-state">No evidence sources were returned.</p>
          ) : (
            report.evidence.map((item) => (
              <article className="evidence-card" key={item.evidence_id}>
                <div className="evidence-title">
                  <FileText size={19} />
                  <strong>{item.source_title}</strong>
                </div>
                <span className="evidence-type">{item.source_type}</span>
                {item.excerpt && <p>{item.excerpt}</p>}
                {item.source_url && (
                  <a href={item.source_url} target="_blank" rel="noreferrer">
                    View source <ExternalLink size={14} />
                  </a>
                )}
              </article>
            ))
          )}
        </section>
      )}

      <footer className="footer">
        ClaimLens · Evidence helps inform decisions; review original sources when possible.
      </footer>
    </main>
  )
}

export default App