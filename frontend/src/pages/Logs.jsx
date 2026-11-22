import { useEffect, useState } from "react";
import { api } from "../api.js";
import { Badge, PageHeader, Spinner, formatDate } from "../components/ui.jsx";

export default function Logs() {
  const [rows, setRows] = useState(null);
  const [filter, setFilter] = useState("ALL");
  useEffect(() => { api.get("/api/logs?limit=300").then(setRows).catch(() => setRows([])); }, []);
  const shown = (rows || []).filter((r) => filter === "ALL" || r.result === filter);
  return (
    <>
      <PageHeader title="Verification logs" subtitle="Every verification attempt. Kept for 90 days (Biometric Data and Privacy Policy).">
        <div className="segmented" role="group" aria-label="Filter by result">
          {["ALL", "MATCH", "UNKNOWN", "NO_FACE"].map((f) => (
            <button key={f} className={filter === f ? "active" : ""} onClick={() => setFilter(f)}>{f}</button>
          ))}
        </div>
      </PageHeader>
      <div className="card table-card">
        {!rows ? <Spinner /> : shown.length === 0 ? <p className="muted pad">No verifications yet.</p> : (
          <table>
            <thead><tr><th>Time</th><th>Checked by</th><th>Result</th><th>Employee</th><th>Model guess</th><th className="num">Similarity</th></tr></thead>
            <tbody>
              {shown.map((r) => (
                <tr key={r.id}>
                  <td>{formatDate(r.created_at)}</td>
                  <td>{r.checked_by}</td>
                  <td><Badge value={r.result} /></td>
                  <td>{r.employee_name || "—"}</td>
                  <td>{r.predicted_label || "—"}</td>
                  <td className="num">{r.result === "NO_FACE" ? "—" : r.similarity.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
