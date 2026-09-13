export function StatusBadge({ status }) {
  const labels = {
    taken: "Taken",
    missed: "Missed",
    skipped: "Skipped",
    due: "Due now",
    overdue: "Overdue",
    upcoming: "Upcoming",
    match: "Appears to match",
    mismatch: "Does not appear to match",
    low_confidence: "Low confidence",
    no_text: "No text",
    expired: "Past saved expiry",
    expiring_soon: "Expiring soon",
    not_scanned: "Not scanned",
    skipped_verification: "Scan skipped",
  };
  const tone =
    status === "taken" || status === "match"
      ? "ok"
      : status === "missed" || status === "mismatch" || status === "overdue" || status === "expired"
        ? "danger"
        : status === "due" || status === "low_confidence" || status === "expiring_soon"
          ? "warn"
          : "muted";
  return <span className={`badge badge-${tone}`}>{labels[status] || status}</span>;
}

export function EmptyState({ title, text, action }) {
  return (
    <div className="empty">
      <h3>{title}</h3>
      <p>{text}</p>
      {action}
    </div>
  );
}

export function LoadingState({ label = "Loading…" }) {
  return (
    <div className="loading" role="status">
      <span className="spinner" />
      {label}
    </div>
  );
}

export function ErrorState({ message }) {
  if (!message) return null;
  return (
    <div className="banner banner-danger" role="alert">
      {message}
    </div>
  );
}

export function SuccessState({ message }) {
  if (!message) return null;
  return (
    <div className="banner banner-ok" role="status">
      {message}
    </div>
  );
}
