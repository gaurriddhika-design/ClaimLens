
interface AuditEvent {
  title: string;
  description: string;
  time?: string;
}

interface AuditTimelineProps {
  events: AuditEvent[];
}

export default function AuditTimeline({
  events,
}: AuditTimelineProps) {
  return (
    <div className="audit-timeline">
      <h2>Verification History</h2>

      {events.length === 0 ? (
        <p>No verification history available.</p>
      ) : (
        <ol>
          {events.map((event, index) => (
            <li key={`${event.title}-${index}`}>
              <h3>{event.title}</h3>
              <p>{event.description}</p>

              {event.time && (
                <small>{event.time}</small>
              )}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
