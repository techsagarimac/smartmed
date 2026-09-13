import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api";
import { ConfirmDialog } from "../components/Modal";
import { EmptyState, ErrorState, LoadingState, StatusBadge } from "../components/StatusBadge";
import { formatClock, formatDate } from "../utils/dates";
import { useToast } from "../hooks/useToast";

export default function Medicines() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState(null);
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  async function load() {
    setError("");
    try {
      setItems(await api.medicines());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function remove() {
    setBusy(true);
    try {
      await api.deleteMedicine(pending.id);
      toast.push("Medicine deleted.", "ok");
      setPending(null);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <LoadingState label="Loading medicines…" />;

  return (
    <div>
      <header className="page-head">
        <div>
          <p className="eyebrow">Library</p>
          <h1>Saved medicines</h1>
          <p className="muted">These records come from information you enter. SmartMed does not prescribe them.</p>
        </div>
        <Link className="btn btn-primary" to="/medicines/new">
          Add medicine
        </Link>
      </header>
      <ErrorState message={error} />
      {items.length === 0 ? (
        <EmptyState
          title="No medicines yet"
          text="Add a medicine name, strength, optional barcode, and at least one schedule to receive reminders."
          action={
            <Link className="btn btn-primary" to="/medicines/new">
              Add medicine
            </Link>
          }
        />
      ) : (
        <div className="card-grid">
          {items.map((item) => (
            <article key={item.id} className="card medicine-card">
              <div className="card-head">
                <h2>{item.name}</h2>
                {item.expired ? <StatusBadge status="expired" /> : item.expiring_soon ? <StatusBadge status="expiring_soon" /> : null}
              </div>
              <p className="strength">{item.strength || "No strength saved"}</p>
              <p>{item.instructions || "No extra instructions saved."}</p>
              <dl className="meta">
                <div>
                  <dt>Expiry saved</dt>
                  <dd>{formatDate(item.expiry_date)}</dd>
                </div>
                <div>
                  <dt>Barcode</dt>
                  <dd>{item.barcode || "Not saved"}</dd>
                </div>
              </dl>
              <ul className="schedule-chips">
                {item.schedules.length === 0 ? <li>No schedule</li> : null}
                {item.schedules.map((schedule) => (
                  <li key={schedule.id}>
                    {formatClock(schedule.time)} · {schedule.frequency.replaceAll("_", " ")}
                  </li>
                ))}
              </ul>
              <div className="row-actions">
                <Link className="btn btn-ghost btn-small" to={`/medicines/${item.id}/edit`}>
                  Edit
                </Link>
                <Link className="btn btn-ghost btn-small" to={`/scan?medicine_id=${item.id}`}>
                  Verify
                </Link>
                <button type="button" className="btn btn-danger btn-small" onClick={() => setPending(item)}>
                  Delete
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
      {pending ? (
        <ConfirmDialog
          title="Delete this medicine?"
          text={`This removes ${pending.name}, its schedules, and dose history from SmartMed. It does not change any real prescription.`}
          confirmLabel="Delete"
          danger
          busy={busy}
          onClose={() => setPending(null)}
          onConfirm={remove}
        />
      ) : null}
    </div>
  );
}
