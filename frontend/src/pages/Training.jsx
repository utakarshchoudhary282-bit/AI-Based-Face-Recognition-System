import { useEffect, useRef, useState } from "react";
import { api } from "../api.js";
import { ConfusionMatrix } from "../components/TrainingCharts.jsx";
import { Notice, PageHeader, Spinner, formatDate } from "../components/ui.jsx";

function Metric({ label, value }) {
  return (
    <div className="stat">
      <div className="stat-value">{(value * 100).toFixed(1)}%</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

export default function Training() {
  const zipInput = useRef(null);
  const [employees, setEmployees] = useState([]);
  const [status, setStatus] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [report, setReport] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const load = () => {
    api.get("/api/employees").then(setEmployees).catch(() => {});
    api.get("/api/train/status").then(setStatus).catch(() => {});
    api.get("/api/train/metrics").then(setMetrics).catch(() => {});
  };
  useEffect(() => { load(); }, []);

  // While training runs, ask for the status every 1.5 seconds.
  useEffect(() => {
    if (status?.state !== "running") return undefined;
    const timer = setInterval(async () => {
      const s = await api.get("/api/train/status").catch(() => null);
      if (s) setStatus(s);
      if (s && s.state !== "running") load();
    }, 1500);
    return () => clearInterval(timer);
  }, [status?.state]);

  async function uploadZip(file) {
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      const form = new FormData();
      form.append("file", file);
      setReport(await api.upload("/api/enroll/zip", form));
      load();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
      zipInput.current.value = "";
    }
  }

  async function train() {
    setError("");
    try {
      setStatus(await api.post("/api/train"));
    } catch (e) {
      setError(e.message);
    }
  }

  const running = status?.state === "running";
  const ready = employees.filter((e) => e.face_images >= 5).length;
  return (
    <>
      <PageHeader title="Enrol & train" subtitle="Upload face photos, train the model, and check how well it recognises each person." />

      <div className="card">
        <h2 className="section-title">1. Upload photos</h2>
        <p className="muted">
          One <strong>.zip</strong> with a folder per person, e.g. <code>project 1/udit/*.jpg</code>. Folder names become
          employees. Each photo's face is found (YuNet), aligned and saved; photos without a face are skipped.
        </p>
        <input ref={zipInput} type="file" accept=".zip" hidden onChange={(e) => uploadZip(e.target.files?.[0])} />
        <button className="btn primary" disabled={busy} onClick={() => zipInput.current.click()}>
          {busy ? <><Spinner /> Processing faces…</> : "Upload zip of person folders"}
        </button>
        {report && (
          <Notice kind={report.total_skipped ? "warning" : "info"}>
            {report.total_saved} faces saved, {report.total_skipped} photos skipped:{" "}
            {report.people.map((p) => `${p.name} ${p.saved}`).join(", ")}.
          </Notice>
        )}
      </div>

      <div className="card">
        <h2 className="section-title">2. Train</h2>
        <div className="face-counts">
          {employees.map((e) => (
            <span key={e.id} className={`count-chip ${e.face_images >= 10 ? "" : e.face_images >= 5 ? "warn" : "bad"}`}>
              {e.name}: {e.face_images}
            </span>
          ))}
        </div>
        <p className="muted small">
          {ready} of {employees.length} people have 5+ photos (needed; 10+ is better). Training turns every face into an
          SFace embedding and fits a logistic regression. It takes a few seconds.
        </p>
        <button className="btn primary" disabled={running || ready < 2} onClick={train}>
          {running ? <><Spinner /> Training…</> : "Train model"}
        </button>
        {status?.message && <Notice kind={status.state === "failed" ? "error" : "info"}>{status.message}</Notice>}
        <Notice kind="error">{error}</Notice>
      </div>

      {metrics && (
        <div className="card">
          <h2 className="section-title">3. How good is it? <span className="muted small">trained {formatDate(metrics.trained_at)}</span></h2>
          <p className="muted small">
            {metrics.num_images} photos of {metrics.people.length} people, {metrics.folds}-fold cross-validation: every photo
            is tested once by a model that never saw it. UNKNOWN below face similarity {metrics.threshold}.
          </p>
          <div className="stat-row">
            <Metric label="Accuracy" value={metrics.accuracy} />
            <Metric label="Precision" value={metrics.precision} />
            <Metric label="Recall" value={metrics.recall} />
            <Metric label="F1 score" value={metrics.f1} />
          </div>
          <ConfusionMatrix matrix={metrics.confusion_matrix} classes={metrics.people} />
          <details>
            <summary>Scores per person</summary>
            <table>
              <thead><tr><th>Person</th><th className="num">Precision</th><th className="num">Recall</th><th className="num">F1</th><th className="num">Photos</th></tr></thead>
              <tbody>
                {metrics.per_person.map((r) => (
                  <tr key={r.person}><td>{r.person}</td><td className="num">{r.precision.toFixed(2)}</td><td className="num">{r.recall.toFixed(2)}</td><td className="num">{r.f1.toFixed(2)}</td><td className="num">{r.photos}</td></tr>
                ))}
              </tbody>
            </table>
          </details>
        </div>
      )}
    </>
  );
}
