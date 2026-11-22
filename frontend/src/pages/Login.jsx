import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api.js";
import { useAuth } from "../App.jsx";
import { Notice, Spinner } from "../components/ui.jsx";

export default function Login() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const [userId, setUserId] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      signIn(await api.login(userId.trim(), password));
      navigate("/verify");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-art" aria-hidden="true">
        <div className="art-inner">
          <img src="/favicon.svg" alt="" width="56" height="56" />
          <h2>Orion Nexus Technologies</h2>
          <p>Face-based employee verification with an AI policy assistant.</p>
          <ul>
            <li>Recognise employees from a photo or webcam</li>
            <li>See access level, status and allowed zones instantly</li>
            <li>Ask policy questions answered from company documents</li>
          </ul>
        </div>
      </div>
      <form className="login-card" onSubmit={submit}>
        <h1>Sign in</h1>
        <p className="muted">Use your portal user ID and password.</p>
        <label>
          User ID
          <input value={userId} onChange={(e) => setUserId(e.target.value)} autoComplete="username" required autoFocus />
        </label>
        <label>
          Password
          <div className="pw">
            <input type={show ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password" required />
            <button type="button" className="link" onClick={() => setShow(!show)}>{show ? "Hide" : "Show"}</button>
          </div>
        </label>
        <Notice kind="error">{error}</Notice>
        <button className="btn primary block" disabled={busy}>{busy ? <><Spinner /> Signing in…</> : "Sign in"}</button>
        <p className="muted small">Accounts are created by an admin. Default admin: admin / Admin@123 (change it in backend/.env).</p>
      </form>
    </div>
  );
}
