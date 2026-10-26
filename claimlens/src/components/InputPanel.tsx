
import { useState } from "react";

interface InputPanelProps {
  claim: string;
  setClaim: (value: string) => void;
  onVerify: () => void;
  isLoading?: boolean;
}

function InputPanel({
  claim,
  setClaim,
  onVerify,
  isLoading = false,
}: InputPanelProps) {
  const [inputMode, setInputMode] = useState<
    "text" | "url" | "image" | "pdf"
  >("text");

  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB
  const handleClear = () => {
    setClaim("");
    setUrl("");
    setFile(null);
    setInputMode("text");
  };
  
const handleVerifyClick = () => {
  if (inputMode === "text" && !claim.trim()) {
    alert("Please enter a claim first.");
    return;
  }

  if (inputMode === "url") {
    if (!url.trim()) {
      alert("Please enter a website URL.");
      return;
    }

    try {
      const parsedUrl = new URL(url);
      if (parsedUrl.protocol !== "http:" && parsedUrl.protocol !== "https:") {
        alert("Please enter a valid HTTP or HTTPS URL.");
        return;
      }
    } catch {
      alert("Please enter a valid website URL.");
      return;
    }

    alert("URL input is ready. Backend integration is still required.");
    return;
  }

  if ((inputMode === "image" || inputMode === "pdf") && !file) {
    alert("Please select a file first.");
    return;
  }
  if (file && file.size > MAX_FILE_SIZE) {
  alert("File size must be 10 MB or less.");
  return;
  }
  if (inputMode === "image" || inputMode === "pdf") {
    alert("File selected. Backend integration is still required.");
    return;
  }

  onVerify();
};

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
      <div className="mb-6">
        <span className="inline-flex rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
          CLAIM VERIFICATION
        </span>

        <h2 className="mt-4 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
          What would you like to verify?
        </h2>

        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          Submit a claim, website link, image, or PDF to begin the verification process.
        </p>
      </div>

      {/* Input mode tabs */}
      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { id: "text", label: "Text", icon: "✍️" },
          { id: "url", label: "Website URL", icon: "🔗" },
          { id: "image", label: "Image", icon: "🖼️" },
          { id: "pdf", label: "PDF Document", icon: "📄" },
        ].map((mode) => (
          <button
            key={mode.id}
            type="button"
            onClick={() =>
              setInputMode(mode.id as "text" | "url" | "image" | "pdf")
            }
            className={`rounded-xl border px-3 py-4 text-sm font-medium transition ${
              inputMode === mode.id
                ? "border-blue-600 bg-blue-50 text-blue-800 ring-2 ring-blue-100"
                : "border-slate-200 bg-white text-slate-600 hover:border-blue-300"
            }`}
          >
            <span className="mb-2 block text-xl">{mode.icon}</span>
            {mode.label}
          </button>
        ))}
      </div>

      {/* Text input */}
      {inputMode === "text" && (
        <div>
          <label htmlFor="claim-input" className="mb-2 block text-sm font-semibold text-slate-700">
            Your claim
          </label>
          <textarea
            id="claim-input"
            value={claim}
            onChange={(event) => setClaim(event.target.value)}
            placeholder="Enter or paste the claim you want to verify..."
            rows={5}
            className="w-full resize-y rounded-xl border border-slate-300 bg-slate-50 px-4 py-3 text-sm leading-6 outline-none focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-100"
          />

          <div className="mt-3">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
              Try an example
            </p>
            <div className="flex flex-wrap gap-2">
              {[
                "The Earth revolves around the Sun.",
                "The Great Wall of China is visible from the Moon.",
                "Drinking water prevents dehydration.",
              ].map((example) => (
                <button
                  key={example}
                  type="button"
                  onClick={() => setClaim(example)}
                  className="rounded-full border border-slate-200 bg-white px-3 py-2 text-left text-xs text-slate-700 hover:border-blue-300 hover:bg-blue-50"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>

          <p className="mt-2 text-right text-xs text-slate-500">
            {claim.length} characters
          </p>
        </div>
      )}

      {/* URL input */}
      {inputMode === "url" && (
        <div>
          <label htmlFor="claim-url" className="mb-2 block text-sm font-semibold text-slate-700">
            Website URL
          </label>
          <input
            id="claim-url"
            type="url"
            value={url}
            onChange={(event) => setUrl(event.target.value)}
            placeholder="https://example.com/news-article"
            className="w-full rounded-xl border border-slate-300 bg-slate-50 px-4 py-3 text-sm focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-100"
          />
          <p className="mt-2 text-xs text-slate-500">
            Paste the link to the article you want to examine.
          </p>
        </div>
      )}

      {/* Image input */}
      {inputMode === "image" && (
        <div>
          <label htmlFor="claim-image" className="mb-2 block text-sm font-semibold text-slate-700">
            Upload an image
          </label>
          <input
            id="claim-image"
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            className="w-full rounded-xl border border-slate-300 bg-slate-50 px-4 py-3 text-sm"
          />
          {file && <p className="mt-2 text-sm text-slate-600">Selected: {file.name}</p>}
        </div>
      )}

      {/* PDF input */}
      {inputMode === "pdf" && (
        <div>
          <label htmlFor="claim-pdf" className="mb-2 block text-sm font-semibold text-slate-700">
            Upload a PDF document
          </label>
          <input
            id="claim-pdf"
            type="file"
            accept="application/pdf"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            className="w-full rounded-xl border border-slate-300 bg-slate-50 px-4 py-3 text-sm"
          />
          {file && <p className="mt-2 text-sm text-slate-600">Selected: {file.name}</p>}
        </div>
      )}

      <div className="mt-5 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={handleVerifyClick}
          disabled={isLoading}
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-700 px-5 py-3 font-semibold text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isLoading ? "Processing..." : "Verify Claim"}
          {!isLoading && <span aria-hidden="true">→</span>}
        </button>

        <button
          type="button"
          onClick={handleClear}
          disabled={isLoading}
          className="rounded-xl border border-slate-300 bg-white px-5 py-3 font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
        >
          Clear
        </button>
      </div>

      <p className="mt-4 text-xs leading-5 text-slate-500">
        Demo mode: actual verification requires a connected backend.
      </p>
    </section>
  );
}

export default InputPanel;
