import { useState } from 'react'
import {
  FileText,
  ShieldCheck,
  LoaderCircle,
  AlertCircle,
  CheckCircle2,
  ExternalLink,
  Image as ImageIcon,
  Link as LinkIcon,
  Type,
} from 'lucide-react'
import './App.css'

type Mode = 'pdf' | 'image' | 'url' | 'text'

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

const API_BASE = 'http://localhost:8000'

const modes: {
  id: Mode
  label: string
  description: string
}[] = [
  { id: 'pdf', label: 'PDF', description: 'Documents' },
  { id: 'image', label: 'Image', description: 'Images and scans' },
  { id: 'url', label: 'URL', description: 'Webpage links' },
  { id: 'text', label: 'Text', description: 'Paste a claim' },
]

function App() {
  const [mode, setMode] = useState<Mode>('pdf')
  const [file, setFile] = useState<File | null>(null)
  const [url, setUrl] = useState('')
  const [text, setText] = useState('')
  const [report, setReport] = useState<Report | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  function changeMode(nextMode: Mode) {
    setMode(nextMode)
    setFile(null)
    setReport(null)
    setError('')
  }

  async function verifyInput() {
    if ((mode === 'pdf' || mode === 'image') && !file) {
      setError(`Please select a ${mode === 'pdf' ? 'PDF' : 'image'} file first.`)
      return
    }

    if (mode === 'url' && !url.trim()) {
      setError('Please enter a webpage URL.')
      return
    }

    if (mode === 'text' && !text.trim()) {
      setError('Please enter some text to verify.')
      return
    }

    setLoading(true)
    setError('')
    setReport(null)

    try {
      let endpoint = ''
      let body: BodyInit

      if (mode === 'pdf') {
        endpoint = '/api/verify/pdf'
        const formData = new FormData()
        formData.append('file', file!)
        body = formData
      } else if (mode === 'image') {
        endpoint = '/api/verify/image'
        const formData = new FormData()
        formData.append('file', file!)
        body = formData
      } else if (mode === 'url') {
        endpoint = '/api/verify/url'
        body = JSON.stringify({ url: url.trim() })
      } else {
        endpoint = '/api/verify'
        body = JSON.stringify({ text: text.trim() })
      }

      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers:
          mode === 'url' || mode === 'text'
            ? { 'Content-Type': 'application/json' }
            : undefined,
        body,
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
        err instanceof TypeError
          ? 'Cannot connect to the backend. Make sure the backend server is running.'
          : err instanceof Error
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
        <span className="topbar-label">AI-POWERED VERIFICATION</span>
      </header>

      <section className="intro">
        <span className="eyebrow">DOCUMENT INTELLIGENCE</span>
        <h1>See beyond the <span>claim.</span></h1>
        <p>
          Check claims using documents, images, webpages, or text.
          Review the available evidence in one place.
        </p>
      </section>

      <section className="upload-card">
        <div className="section-heading">
          <span className="step-number">01</span>
          <div>
            <h2>Choose your input</h2>
            <p>Select how you want to submit information for verification.</p>
          </div>
        </div>

        <div className="mode-tabs">
          {modes.map((item) => (
            <button
              type="button"
              key={item.id}
              className={`mode-tab ${mode === item.id ? 'active' : ''}`}
              onClick={() => changeMode(item.id)}
              disabled={loading}
            >
              {item.id === 'pdf' && <FileText size={19} />}
              {item.id === 'image' && <ImageIcon size={19} />}
              {item.id === 'url' && <LinkIcon size={19} />}
              {item.id === 'text' && <Type size={19} />}
              <span>{item.label}</span>
              <small>{item.description}</small>
            </button>
          ))}
        </div>

        {(mode === 'pdf' || mode === 'image') && (
          <label className="dropzone">
            <input
              type="file"
              accept={mode === 'pdf' ? '.pdf,application/pdf' : 'image/*'}
              onChange={(event) => {
                setFile(event.target.files?.[0] ?? null)
                setReport(null)
                setError('')
              }}
            />
            <span className="upload-icon">
              {mode === 'pdf' ? <FileText size={25} /> : <ImageIcon size={25} />}
            </span>
            <strong>
              {file
                ? file.name
                : mode === 'pdf'
                  ? 'Choose a PDF document'
                  : 'Choose an image'}
            </strong>
            <span className="file-hint">
              {file
                ? `${(file.size / (1024 * 1024)).toFixed(2)} MB`
                : mode === 'pdf'
                  ? 'PDF format · Scanned PDFs supported through OCR'
                  : 'PNG, JPG, JPEG, or another browser-supported image'}
            </span>
          </label>
        )}

        {mode === 'url' && (
          <div className="field-group">
            <label htmlFor="source-url">Webpage URL</label>
            <input
              id="source-url"
              className="text-input"
              type="url"
              placeholder="https://example.com/article"
              value={url}
              onChange={(event) => setUrl(event.target.value)}
            />
            <p className="field-hint">Enter the link to the webpage you want to check.</p>
          </div>
        )}

        {mode === 'text' && (
          <div className="field-group">
            <label htmlFor="claim-text">Text or claim</label>
            <textarea
              id="claim-text"
              className="text-input text-area"
              placeholder="Paste the claim or paragraph you want to verify..."
              value={text}
              onChange={(event) => setText(event.target.value)}
              rows={6}
            />
          </div>
        )}

        <button
          type="button"
          className="verify-button"
          onClick={verifyInput}
          disabled={
            loading ||
            ((mode === 'pdf' || mode === 'image') && !file)
          }
        >
          {loading ? (
            <><LoaderCircle className="spin" size={19} /> Verifying...</>
          ) : (
            <><ShieldCheck size={19} /> Verify {mode === 'url' ? 'URL' : mode === 'text' ? 'text' : mode === 'image' ? 'image' : 'document'}</>
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
          Your input is being processed. This may take a little time.
        </p>
      )}

      {report && (
        <section className="results">
          <div className="results-heading">
            <div>
              <span className="eyebrow">VERIFICATION REPORT</span>
              <h2>Results</h2>
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
                <p className="source-location">Location: {claim.source_location}</p>
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
        ClaimLens · Evidence can inform decisions; review original sources when possible.
      </footer>
    </main>
  )
}

export default App