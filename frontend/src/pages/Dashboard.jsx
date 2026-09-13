import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { CalendarClock, CheckCircle2, Percent, TriangleAlert } from "lucide-react";
import { api } from "../services/api";
import { EmptyState, ErrorState, LoadingState, StatusBadge } from "../components/StatusBadge";
import { formatClock, formatDate, formatDateTime } from "../utils/dates";
import { useAuth } from "../hooks/useAuth";

export default function Dashboard() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    api
      .analytics()
      .then((payload) => {
        if (!cancelled) setData(payload);
      })
      .catch((err) => {
        if (err.status === 401) logout();
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [logout]);

  if (loading) return <LoadingState label="Loading dashboard…" />;
  if (error) return <ErrorState message={error} />;
  if (!data) return <EmptyState title="Dashboard unavailable" text="No analytics were returned." />;

  return (
    <div>
      <header className="page-head">
        <div>
          <p className="eyebrow">Today</p>
          <h1>Medication dashboard</h1>
          <p className="muted">Reminders use the schedules you saved. Verification compares package scans with those records.</p>
        </div>
        <Link to="/scan" className="btn btn-primary">
          Verify a medicine
        </Link>
      </header>

      <section className="stat-grid">
        <article className="stat-card">
          <CheckCircle2 size={20} />
          <span>Taken today</span>
          <strong>{data.taken_count}</strong>
        </article>
        <article className="stat-card warn">
          <TriangleAlert size={20} />
          <span>Missed today</span>
          <strong>{data.missed_count}</strong>
        </article>
        <article className="stat-card">
          <Percent size={20} />
          <span>7-day adherence</span>
          <strong>{data.adherence_percentage}%</strong>
          <small>Taken ÷ (taken + missed)</small>
        </article>
        <article className="stat-card">
          <CalendarClock size={20} />
          <span>Upcoming</span>
          <strong>{data.upcoming ? formatClock(data.upcoming.scheduled_time) : "—"}</strong>
          <small>{data.upcoming ? data.upcoming.medicine_name : "No upcoming slot"}</small>
        </article>
      </section>

      <div className="split">
        <section className="card">
          <div className="card-head">
            <h2>Today’s medicines</h2>
          </div>
          {data.today_medicines.length === 0 ? (
            <EmptyState
              title="No schedules for today"
              text="Add a medicine and a daily or weekly time to see reminders here."
              action={
                <Link className="btn btn-primary" to="/medicines/new">
                  Add medicine
                </Link>
              }
            />
          ) : (
            <ul className="dose-list">
              {data.today_medicines.map((item) => (
                <li key={`${item.medicine_id}-${item.scheduled_time}`}>
                  <div>
                    <strong>{item.medicine_name}</strong>
                    <span className="muted">
                      {item.strength} · {formatClock(item.scheduled_time)}
                    </span>
                  </div>
                  <StatusBadge status={item.status} />
                  {item.status === "taken" || item.status === "skipped" ? null : (
                    <button
                      type="button"
                      className="btn btn-small btn-primary"
                      onClick={() =>
                        navigate(
                          `/scan?medicine_id=${item.medicine_id}&scheduled_time=${encodeURIComponent(item.scheduled_time)}`,
                        )
                      }
                    >
                      Verify
                    </button>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="card">
          <div className="card-head">
            <h2>Expiring medicines</h2>
          </div>
          {data.expiring_medicines.length === 0 ? (
            <p className="muted">No saved medicines are near the expiry date you entered.</p>
          ) : (
            <ul className="plain-list">
              {data.expiring_medicines.map((item) => (
                <li key={item.id}>
                  <div>
                    <strong>{item.name}</strong>
                    <span className="muted">Saved expiry {formatDate(item.expiry_date)}</span>
                  </div>
                  <StatusBadge status={item.expired ? "expired" : "expiring_soon"} />
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <section className="card">
        <div className="card-head">
          <h2>Recent dose history</h2>
          <Link to="/history">View all</Link>
        </div>
        {data.recent_history.length === 0 ? (
          <p className="muted">No doses recorded yet.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Medicine</th>
                  <th>Scheduled</th>
                  <th>Status</th>
                  <th>Verification</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_history.map((row) => (
                  <tr key={row.id}>
                    <td>
                      {row.medicine_name}
                      {row.medicine_strength ? ` · ${row.medicine_strength}` : ""}
                    </td>
                    <td>{formatDateTime(row.scheduled_time)}</td>
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
      </section>

      {!data.ocr_available ? (
        <div className="banner banner-warn">
          Tesseract OCR is not available on the server. Photo verification will show a setup error until
          Tesseract is installed. Barcode-only comparison can still be used.
        </div>
      ) : null}
    </div>
  );
}
