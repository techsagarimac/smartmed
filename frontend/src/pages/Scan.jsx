import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Html5Qrcode } from "html5-qrcode";
import { api } from "../services/api";
import { CameraCapture } from "../components/CameraCapture";
import { ConfirmDialog } from "../components/Modal";
import { ErrorState, LoadingState, StatusBadge } from "../components/StatusBadge";
import { formatClock } from "../utils/dates";
import { useToast } from "../hooks/useToast";

export default function Scan() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const toast = useToast();
  const [medicines, setMedicines] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [medicineId, setMedicineId] = useState(params.get("medicine_id") || "");
  const [scheduledTime, setScheduledTime] = useState(params.get("scheduled_time") || "");
  const [tab, setTab] = useState("photo");
  const [preview, setPreview] = useState("");
  const [blob, setBlob] = useState(null);
  const [barcode, setBarcode] = useState("");
  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [skipOpen, setSkipOpen] = useState(false);
  const scannerRef = useRef(null);
  const boxRef = useRef(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([api.medicines(), api.reminders()])
      .then(([meds, slots]) => {
        if (cancelled) return;
        setMedicines(meds);
        setReminders(slots);
        setMedicineId((current) => current || (meds[0] ? String(meds[0].id) : ""));
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
  }, []);

  const selected = medicines.find((item) => String(item.id) === String(medicineId));
  const matchingSlots = reminders.filter((item) => String(item.medicine_id) === String(medicineId));

  useEffect(() => {
    const exists = matchingSlots.some((item) => item.scheduled_time === scheduledTime);
    if (!exists) {
      setScheduledTime(matchingSlots[0]?.scheduled_time || "");
    }
  }, [matchingSlots, scheduledTime]);

  useEffect(() => {
    return () => stopBarcode();
  }, []);

  function onCapture(nextBlob) {
    setBlob(nextBlob);
    setPreview(URL.createObjectURL(nextBlob));
    setResult(null);
  }

  function onFile(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setBlob(file);
    setPreview(URL.createObjectURL(file));
    setResult(null);
  }

  async function startBarcode() {
    setError("");
    try {
      if (!boxRef.current) return;
      const scanner = new Html5Qrcode(boxRef.current.id);
      scannerRef.current = scanner;
      await scanner.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: { width: 260, height: 160 } },
        (decoded) => {
          setBarcode(decoded);
          toast.push("Barcode read from camera.", "ok");
          stopBarcode();
        },
      );
    } catch (err) {
      setError(err.message || "Barcode camera could not start. Type the barcode or use a package photo.");
    }
  }

  async function stopBarcode() {
    const scanner = scannerRef.current;
    if (!scanner) return;
    try {
      await scanner.stop();
      await scanner.clear();
    } catch {
      /* already stopped */
    }
    scannerRef.current = null;
  }

  async function runScan() {
    if (!medicineId) {
      setError("Select the saved medicine you intend to compare against.");
      return;
    }
    if (!blob && !barcode.trim()) {
      setError("Capture or upload a package photo, or enter a barcode.");
      return;
    }
    setScanning(true);
    setError("");
    try {
      const form = new FormData();
      form.append("medicine_id", medicineId);
      if (barcode.trim()) form.append("barcode", barcode.trim());
      if (blob) form.append("file", blob, "capture.jpg");
      const payload = await api.scan(form);
      setResult(payload);
    } catch (err) {
      setError(err.message);
    } finally {
      setScanning(false);
    }
  }

  async function record(status, verification) {
    if (!scheduledTime) {
      setError("Choose the scheduled time this dose belongs to.");
      return;
    }
    setScanning(true);
    setError("");
    try {
      await api.recordDose({
        medicine_id: Number(medicineId),
        scheduled_time: scheduledTime,
        status,
        verification_result: verification,
      });
      toast.push(status === "taken" ? "Dose recorded." : "Dose marked skipped.", "ok");
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setScanning(false);
      setSkipOpen(false);
    }
  }

  if (loading) return <LoadingState label="Loading scan workspace…" />;

  return (
    <div>
      <header className="page-head">
        <div>
          <p className="eyebrow">Verification</p>
          <h1>Scan a saved medicine</h1>
          <p className="muted">
            This compares detected package text or a barcode with the medicine record you selected. A match
            means the labels appear similar, not that the medicine is authentic or safe.
          </p>
        </div>
      </header>
      <ErrorState message={error} />

      <div className="split">
        <section className="card">
          <label>
            Saved medicine to compare
            <select value={medicineId} onChange={(e) => setMedicineId(e.target.value)}>
              <option value="">Select a medicine</option>
              {medicines.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name} {item.strength}
                </option>
              ))}
            </select>
          </label>
          <label>
            Scheduled time
            <select value={scheduledTime} onChange={(e) => setScheduledTime(e.target.value)}>
              <option value="">Select a slot</option>
              {matchingSlots.map((item) => (
                <option key={item.scheduled_time} value={item.scheduled_time}>
                  {formatClock(item.scheduled_time)} · {item.status}
                </option>
              ))}
            </select>
          </label>
          {matchingSlots.length === 0 ? (
            <label>
              Or enter the scheduled time
              <input
                type="datetime-local"
                value={scheduledTime ? scheduledTime.slice(0, 16) : ""}
                onChange={(e) => setScheduledTime(e.target.value ? `${e.target.value}:00` : "")}
              />
            </label>
          ) : null}
          {selected?.expired ? <StatusBadge status="expired" /> : null}
          {selected?.instructions ? <p className="muted">{selected.instructions}</p> : null}

          <div className="segmented">
            <button type="button" className={tab === "photo" ? "active" : ""} onClick={() => setTab("photo")}>
              Package photo
            </button>
            <button type="button" className={tab === "barcode" ? "active" : ""} onClick={() => setTab("barcode")}>
              Barcode
            </button>
          </div>

          {tab === "photo" ? (
            <>
              <CameraCapture onCapture={onCapture} disabled={scanning} />
              <label className="file-label">
                Or upload a package photo
                <input type="file" accept="image/*" capture="environment" onChange={onFile} />
              </label>
              {preview ? <img src={preview} alt="Captured medicine package" className="preview" /> : null}
            </>
          ) : (
            <>
              <div id="barcode-box" ref={boxRef} className="barcode-box" />
              <div className="row-actions">
                <button type="button" className="btn btn-ghost" onClick={startBarcode}>
                  Start barcode camera
                </button>
                <button type="button" className="btn btn-ghost" onClick={stopBarcode}>
                  Stop
                </button>
              </div>
              <label>
                Barcode value
                <input value={barcode} onChange={(e) => setBarcode(e.target.value)} placeholder="Scan or type the printed barcode" />
              </label>
            </>
          )}

          <div className="row-actions">
            <button type="button" className="btn btn-primary" onClick={runScan} disabled={scanning}>
              {scanning ? "Reading package…" : "Compare with saved medicine"}
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => setSkipOpen(true)}>
              Skip scan
            </button>
          </div>
        </section>

        <section className="card result-card">
          {!result ? (
            <p className="muted">Capture a label or barcode, then compare. Results appear here.</p>
          ) : (
            <VerificationResult
              result={result}
              onRecord={() => record("taken", "match")}
              onAgain={() => setResult(null)}
              scanning={scanning}
            />
          )}
        </section>
      </div>

      {skipOpen ? (
        <ConfirmDialog
          title="Skip verification?"
          text="You can record this slot as skipped without comparing a package. SmartMed will not assume you took the medicine."
          confirmLabel="Mark skipped"
          onClose={() => setSkipOpen(false)}
          onConfirm={() => record("skipped", "skipped_verification")}
          busy={scanning}
        />
      ) : null}
    </div>
  );
}

function VerificationResult({ result, onRecord, onAgain, scanning }) {
  const matched = result.result === "match";
  return (
    <div>
      <p className="eyebrow">{matched ? "Possible match" : "Check the package"}</p>
      <h2>{result.headline}</h2>
      <div className="compare">
        <div>
          <h3>{matched ? "Scheduled medicine" : "Expected medicine"}</h3>
          <p>
            <strong>{result.scheduled_medicine.name}</strong>
            <br />
            {result.scheduled_medicine.strength || "No strength saved"}
            <br />
            {result.scheduled_medicine.barcode || "No barcode saved"}
          </p>
        </div>
        <div>
          <h3>Detected medicine</h3>
          <p>
            <strong>{result.detected.name || "No name read"}</strong>
            <br />
            {result.detected.strength || "No strength read"}
            <br />
            {result.detected.barcode || "No barcode read"}
          </p>
        </div>
      </div>
      {result.confidence != null ? (
        <p className="muted">Scan confidence {Math.round(result.confidence * 100)}% · name similarity {Math.round((result.name_similarity || 0) * 100)}%</p>
      ) : null}
      {result.detected.raw_text ? <pre className="ocr-text">{result.detected.raw_text}</pre> : null}
      <div className="banner banner-muted">{result.guidance}</div>
      <p className="notice notice-compact">{result.disclaimer}</p>
      <div className="row-actions">
        {result.can_record_dose ? (
          <button type="button" className="btn btn-primary" onClick={onRecord} disabled={scanning}>
            Record dose
          </button>
        ) : (
          <button type="button" className="btn btn-primary" onClick={onAgain}>
            Scan again
          </button>
        )}
      </div>
    </div>
  );
}
