import { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { SafetyNotice } from "../components/SafetyNotice";
import { ErrorState } from "../components/StatusBadge";

export default function Register() {
  const { register, isAuthenticated } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (isAuthenticated) return <Navigate to="/" replace />;

  async function onSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await register(name.trim(), email.trim(), password);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-shell">
      <section className="auth-panel">
        <div className="brand-mark lg">SM</div>
        <p className="eyebrow">Create your records</p>
        <h1>Register the medicines you already have.</h1>
        <p className="lead">
          Add names, strengths, schedules, and optional barcodes from your prescription or package. SmartMed
          will remind you and help compare later scans with those saved details.
        </p>
        <SafetyNotice />
      </section>
      <form className="auth-card" onSubmit={onSubmit}>
        <h2>Create account</h2>
        <ErrorState message={error} />
        <label>
          Full name
          <input value={name} onChange={(e) => setName(e.target.value)} minLength={2} required />
        </label>
        <label>
          Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label>
          Password
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={8} required />
        </label>
        <button type="submit" className="btn btn-primary btn-block" disabled={busy}>
          {busy ? "Creating account…" : "Create account"}
        </button>
        <p className="muted center">
          Already registered? <Link to="/login">Sign in</Link>
        </p>
      </form>
    </div>
  );
}
