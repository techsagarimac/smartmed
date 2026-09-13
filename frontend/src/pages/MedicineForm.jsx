import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../services/api";
import { ErrorState, LoadingState, SuccessState } from "../components/StatusBadge";
import { todayISO, toTimeInput } from "../utils/dates";
import { useToast } from "../hooks/useToast";

const emptySchedule = () => ({
  time: "08:00",
  frequency: "daily",
  start_date: todayISO(),
  end_date: "",
});

export default function MedicineForm() {
  const { id } = useParams();
  const editing = Boolean(id);
  const navigate = useNavigate();
  const toast = useToast();
  const [loading, setLoading] = useState(editing);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [form, setForm] = useState({
    name: "",
    strength: "",
    instructions: "",
    expiry_date: "",
    barcode: "",
  });
  const [schedules, setSchedules] = useState([emptySchedule()]);
  const [savedSchedules, setSavedSchedules] = useState([]);

  useEffect(() => {
    if (!editing) return undefined;
    let cancelled = false;
    api
      .medicine(id)
      .then((item) => {
        if (cancelled) return;
        setForm({
          name: item.name,
          strength: item.strength || "",
          instructions: item.instructions || "",
          expiry_date: item.expiry_date || "",
          barcode: item.barcode || "",
        });
        setSavedSchedules(item.schedules || []);
        setSchedules([]);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [editing, id]);

  function updateField(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function onSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const payload = {
        name: form.name.trim(),
        strength: form.strength.trim(),
        instructions: form.instructions.trim(),
        expiry_date: form.expiry_date || null,
        barcode: form.barcode.trim() || null,
      };
      if (editing) {
        await api.updateMedicine(id, payload);
        for (const schedule of schedules) {
          if (!schedule.time) continue;
          await api.createSchedule({
            medicine_id: Number(id),
            time: `${schedule.time}:00`,
            frequency: schedule.frequency,
            start_date: schedule.start_date,
            end_date: schedule.end_date || null,
          });
        }
        toast.push("Medicine updated.", "ok");
        setMessage("Medicine updated. New schedule rows were added if you filled them.");
        const refreshed = await api.medicine(id);
        setSavedSchedules(refreshed.schedules || []);
        setSchedules([]);
      } else {
        const created = await api.createMedicine({
          ...payload,
          schedules: schedules
            .filter((item) => item.time && item.start_date)
            .map((item) => ({
              time: `${item.time}:00`,
              frequency: item.frequency,
              start_date: item.start_date,
              end_date: item.end_date || null,
            })),
        });
        toast.push("Medicine saved.", "ok");
        navigate(`/medicines/${created.id}/edit`);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function removeSchedule(scheduleId) {
    setBusy(true);
    setError("");
    try {
      await api.deleteSchedule(scheduleId);
      setSavedSchedules((current) => current.filter((item) => item.id !== scheduleId));
      toast.push("Schedule removed.", "ok");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <LoadingState label="Loading medicine…" />;

  return (
    <div className="narrow">
      <header className="page-head">
        <div>
          <p className="eyebrow">{editing ? "Edit" : "New"}</p>
          <h1>{editing ? "Edit medicine" : "Add medicine"}</h1>
          <p className="muted">Enter details from the package or prescription you already have. SmartMed will not suggest a drug or dose.</p>
        </div>
        <Link to="/medicines" className="btn btn-ghost">
          Back
        </Link>
      </header>
      <ErrorState message={error} />
      <SuccessState message={message} />
      <form className="card form" onSubmit={onSubmit}>
        <label>
          Medicine name
          <input value={form.name} onChange={(e) => updateField("name", e.target.value)} required />
        </label>
        <div className="form-grid">
          <label>
            Strength
            <input value={form.strength} onChange={(e) => updateField("strength", e.target.value)} placeholder="500 mg" />
          </label>
          <label>
            Expiry date
            <input type="date" value={form.expiry_date} onChange={(e) => updateField("expiry_date", e.target.value)} />
          </label>
        </div>
        <label>
          Optional barcode
          <input value={form.barcode} onChange={(e) => updateField("barcode", e.target.value)} placeholder="Printed package barcode" />
        </label>
        <label>
          Instructions (as already prescribed)
          <textarea rows={3} value={form.instructions} onChange={(e) => updateField("instructions", e.target.value)} />
        </label>

        {editing ? (
          <section>
            <h2>Saved schedules</h2>
            {savedSchedules.length === 0 ? <p className="muted">No schedule rows yet.</p> : null}
            <ul className="plain-list">
              {savedSchedules.map((item) => (
                <li key={item.id}>
                  <span>
                    {toTimeInput(item.time)} · {item.frequency.replaceAll("_", " ")} · from {item.start_date}
                    {item.end_date ? ` to ${item.end_date}` : ""}
                  </span>
                  <button type="button" className="btn btn-ghost btn-small" onClick={() => removeSchedule(item.id)} disabled={busy}>
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        <section>
          <div className="card-head">
            <h2>{editing ? "Add another schedule" : "Schedule"}</h2>
            <button type="button" className="btn btn-ghost btn-small" onClick={() => setSchedules((current) => [...current, emptySchedule()])}>
              Add time
            </button>
          </div>
          <p className="muted">Use one row per clock time. Morning and evening doses are two rows, both daily.</p>
          {schedules.map((item, index) => (
            <div className="form-grid schedule-row" key={index}>
              <label>
                Time
                <input type="time" value={item.time} onChange={(e) => setSchedules(updateAt(schedules, index, { time: e.target.value }))} />
              </label>
              <label>
                Frequency
                <select value={item.frequency} onChange={(e) => setSchedules(updateAt(schedules, index, { frequency: e.target.value }))}>
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="every_other_day">Every other day</option>
                </select>
              </label>
              <label>
                Start date
                <input type="date" value={item.start_date} onChange={(e) => setSchedules(updateAt(schedules, index, { start_date: e.target.value }))} />
              </label>
              <label>
                End date (optional)
                <input type="date" value={item.end_date} onChange={(e) => setSchedules(updateAt(schedules, index, { end_date: e.target.value }))} />
              </label>
            </div>
          ))}
        </section>

        <button type="submit" className="btn btn-primary" disabled={busy}>
          {busy ? "Saving…" : editing ? "Save changes" : "Save medicine"}
        </button>
      </form>
    </div>
  );
}

function updateAt(list, index, patch) {
  return list.map((item, i) => (i === index ? { ...item, ...patch } : item));
}
