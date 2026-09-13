import { useEffect, useState } from "react";
import { api } from "../services/api";
import { EmptyState, ErrorState, LoadingState, StatusBadge } from "../components/StatusBadge";
import { formatDateTime } from "../utils/dates";

export default function History() {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    api
      .doseHistory()
      .then(setRows)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingState label="Loading dose history…" />;

  const visible = rows.filter((row) => (filter === "all" ? true : row.status === filter));

  return (
    <div>
      <header className="page-head">
        <div>
          <p className="eyebrow">Log</p>
          <h1>Dose history</h1>
          <p className="muted">Taken, missed, and skipped records for the medicines you saved.</p>
        </div>
        <select value={filter} onChange={(e) => setFilter(e.target.value)} aria-label="Filter history">
          <option value="all">All statuses</option>
          <option value="taken">Taken</option>
          <option value="missed">Missed</option>
          <option value="skipped">Skipped</option>
        </select>
      </header>
      <ErrorState message={error} />
      {visible.length === 0 ? (
        <EmptyState title="No history yet" text="Record a dose from the scan page after comparing a package with a saved medicine." />
      ) : (
        <div className="card table-wrap">
          <table>
            <thead>
              <tr>
                <th>Medicine</th>
                <th>Scheduled</th>
                <th>Recorded</th>
                <th>Status</th>
                <th>Verification</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((row) => (
                <tr key={row.id}>
                  <td>
                    {row.medicine_name}
                    {row.medicine_strength ? ` · ${row.medicine_strength}` : ""}
                  </td>
                  <td>{formatDateTime(row.scheduled_time)}</td>
                  <td>{row.actual_time ? formatDateTime(row.actual_time) : "—"}</td>
                  <td>
                    <StatusBadge status={row.status} />
                  </td>
                  <td>
                    <StatusBadge status={row.verification_result || "not_scanned"} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
