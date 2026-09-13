import { useEffect, useState } from "react";
import { api } from "../services/api";
import { ConfirmDialog } from "../components/Modal";
import { EmptyState, ErrorState, LoadingState, SuccessState } from "../components/StatusBadge";
import { useToast } from "../hooks/useToast";

const empty = { caregiver_name: "", caregiver_contact: "", notifications_enabled: true };

export default function Caregivers() {
  const toast = useToast();
  const [items, setItems] = useState([]);
  const [form, setForm] = useState(empty);
  const [delivery, setDelivery] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [pending, setPending] = useState(null);

  async function load() {
    try {
      const [rows, status] = await Promise.all([api.caregivers(), api.caregiverDelivery()]);
      setItems(rows);
      setDelivery(status);
      setError("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function onSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api.createCaregiver(form);
      setForm(empty);
      toast.push("Caregiver saved.", "ok");
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function toggle(item) {
    try {
      await api.updateCaregiver(item.id, { notifications_enabled: !item.notifications_enabled });
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function remove() {
    setBusy(true);
    try {
      await api.deleteCaregiver(pending.id);
      setPending(null);
      toast.push("Caregiver removed.", "ok");
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <LoadingState label="Loading caregivers…" />;

  return (
    <div className="narrow">
      <header className="page-head">
        <div>
          <p className="eyebrow">Optional</p>
          <h1>Caregivers</h1>
          <p className="muted">
            If a scheduled dose is recorded as missed, SmartMed can notify these contacts. Messages are
            schedule alerts only, not medical advice.
          </p>
        </div>
      </header>
      <ErrorState message={error} />
      {delivery ? <SuccessState message={delivery.detail} /> : null}

      <form className="card form" onSubmit={onSubmit}>
        <h2>Add a caregiver</h2>
        <label>
          Name
          <input value={form.caregiver_name} onChange={(e) => setForm({ ...form, caregiver_name: e.target.value })} required />
        </label>
        <label>
          Email or phone
          <input
            value={form.caregiver_contact}
            onChange={(e) => setForm({ ...form, caregiver_contact: e.target.value })}
            required
            placeholder="email@example.com"
          />
        </label>
        <label className="check">
          <input
            type="checkbox"
            checked={form.notifications_enabled}
            onChange={(e) => setForm({ ...form, notifications_enabled: e.target.checked })}
          />
          Enable missed-dose alerts
        </label>
        <button type="submit" className="btn btn-primary" disabled={busy}>
          {busy ? "Saving…" : "Save caregiver"}
        </button>
      </form>

      {items.length === 0 ? (
        <EmptyState title="No caregivers yet" text="Add a family member or carer if you want missed-dose alerts." />
      ) : (
        <ul className="plain-list card">
          {items.map((item) => (
            <li key={item.id}>
              <div>
                <strong>{item.caregiver_name}</strong>
                <span className="muted">{item.caregiver_contact}</span>
              </div>
              <div className="row-actions">
                <button type="button" className="btn btn-ghost btn-small" onClick={() => toggle(item)}>
                  {item.notifications_enabled ? "Disable alerts" : "Enable alerts"}
                </button>
                <button type="button" className="btn btn-danger btn-small" onClick={() => setPending(item)}>
                  Remove
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {pending ? (
        <ConfirmDialog
          title="Remove caregiver?"
          text={`Remove ${pending.caregiver_name} from missed-dose alerts?`}
          confirmLabel="Remove"
          danger
          busy={busy}
          onClose={() => setPending(null)}
          onConfirm={remove}
        />
      ) : null}
    </div>
  );
}
