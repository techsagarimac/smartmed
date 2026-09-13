import { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { SafetyNotice } from "../components/SafetyNotice";
import { ErrorState } from "../components/StatusBadge";

export default function Login() {
  const { login, isAuthenticated } = useAuth();
  const [email, setEmail] = useState("demo@smartmed.local");
  const [password, setPassword] = useState("DemoPass123");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (isAuthenticated) return <Navigate to="/" replace />;

  async function onSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(email.trim(), password);
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
        <p className="eyebrow">College major project</p>
        <h1>Remember the dose. Verify the package.</h1>
        <p className="lead">
          SmartMed reminds you about medicines you already registered and compares a scanned label with that
          saved record. It does not decide what you should take.
        </p>
        <SafetyNotice />
      </section>
      <form className="auth-card" onSubmit={onSubmit}>
        <h2>Sign in</h2>
        <p className="muted">Use your account, or the seeded demo login.</p>
        <ErrorState message={error} />
        <label>
          Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="username" />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />
        </label>
        <button type="submit" className="btn btn-primary btn-block" disabled={busy}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
        <p className="muted center">
          New here? <Link to="/register">Create an account</Link>
        </p>
      </form>
    </div>
  );
}
