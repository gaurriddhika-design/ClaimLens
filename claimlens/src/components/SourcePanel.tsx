
interface Source {
  title: string;
  url: string;
  publisher?: string;
}

interface SourcePanelProps {
  sources: Source[];
}

export default function SourcePanel({
  sources,
}: SourcePanelProps) {
  return (
    <div className="source-panel">
      <h2>Verification Sources</h2>

      {sources.length === 0 ? (
        <p>No sources available yet.</p>
      ) : (
        <ul>
          {sources.map((source, index) => (
            <li key={`${source.url}-${index}`}>
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
              >
                {source.title}
              </a>

              {source.publisher && (
                <p>{source.publisher}</p>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
