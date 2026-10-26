
interface AnalysisProgressProps {
  progress: number;
  message?: string;
}

export default function AnalysisProgress({
  progress,
  message = 'Analyzing claim...',
}: AnalysisProgressProps) {
  const safeProgress = Math.min(
    100,
    Math.max(0, progress)
  );

  return (
    <div className="analysis-progress">
      <div className="progress-header">
        <span>{message}</span>
        <span>{safeProgress}%</span>
      </div>

      <div
        className="progress-track"
        role="progressbar"
        aria-label="Claim analysis progress"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={safeProgress}
      >
        <div
          className="progress-fill"
          style={{ width: `${safeProgress}%` }}
        />
      </div>
    </div>
  );
}
