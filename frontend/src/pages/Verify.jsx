import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import { useAuth } from "../App.jsx";
import ChatPanel from "../components/ChatPanel.jsx";
import PhotoCapture from "../components/PhotoCapture.jsx";
import ResultCard from "../components/ResultCard.jsx";
import { Notice, PageHeader, Spinner } from "../components/ui.jsx";

export default function Verify() {
  const { user } = useAuth();
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [stats, setStats] = useState(null);

  useEffect(() => { api.get("/api/stats").then(setStats).catch(() => {}); }, [result]);

  function choose(f) {
    setFile(f);
    setResult(null);
    setError("");
  }

  async function verify() {
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      const form = new FormData();
      form.append("file", file);
      setResult(await api.upload("/api/verify", form));
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  const emp = result?.employee;
  return (
    <>
      <PageHeader title="Verify a person" subtitle="Upload or capture a photo. The model finds the face and returns the matching employee." />
      {stats && !stats.model_ready && (
        <Notice kind="warning">
          No face model is trained yet.{" "}
          {user.role === "admin" ? <Link to="/training">Upload photos and train the model</Link> : "Ask an admin to enrol employees and train the model."}
        </Notice>
      )}
      {stats && (
        <div className="stat-row">
          <div className="stat"><div className="stat-value">{stats.employees}</div><div className="stat-label">Employees</div></div>
          <div className="stat"><div className="stat-value">{stats.people_in_model}</div><div className="stat-label">People in model</div></div>
          <div className="stat"><div className="stat-value">{stats.checks_today}</div><div className="stat-label">Checks today</div></div>
          <div className="stat"><div className="stat-value">{stats.match_rate == null ? "—" : `${Math.round(stats.match_rate * 100)}%`}</div><div className="stat-label">Match rate (all time)</div></div>
        </div>
      )}
      <div className="grid-2">
        <div className="card">
          <PhotoCapture file={file} onChange={choose} faceBox={result?.face_box} />
          <button className="btn primary block" disabled={!file || busy} onClick={verify}>
            {busy ? <><Spinner /> Verifying…</> : "Verify identity"}
          </button>
          <Notice kind="error">{error}</Notice>
        </div>
        <ResultCard result={result} />
      </div>
      {emp && (
        <section className="card">
          <h2 className="section-title">Ask about {emp.name}</h2>
          <ChatPanel employee={emp} compact suggestions={[
            "Can this employee enter the server room?",
            "Is entry allowed today given their status?",
            "What are their shift timings and the late-mark rule?",
            "What should I do if verification fails?",
          ]} />
        </section>
      )}
    </>
  );
}
