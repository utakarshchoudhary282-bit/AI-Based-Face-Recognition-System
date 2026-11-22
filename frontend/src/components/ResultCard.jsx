import { AuthImage, Badge, LevelChip } from "./ui.jsx";

function SimilarityBar({ value, threshold }) {
  const v = Math.max(0, Math.min(1, value));
  return (
    <div className="conf">
      <div className="conf-track" role="meter" aria-label="Face similarity" aria-valuenow={Math.round(v * 100)}
        aria-valuemin={0} aria-valuemax={100}>
        <div className={`conf-fill ${value >= threshold ? "ok" : "low"}`} style={{ width: `${v * 100}%` }} />
        <div className="conf-threshold" style={{ left: `${threshold * 100}%` }} title={`Threshold ${threshold}`} />
      </div>
      <span className="conf-label">
        Face similarity {value.toFixed(2)} <span className="muted">(match needs ≥ {threshold.toFixed(2)})</span>
      </span>
    </div>
  );
}

const FIELDS = [
  ["Employee code", "employee_code"], ["Department", "department"], ["Designation", "designation"],
  ["Shift", "shift"], ["Office", "office_location"], ["Manager", "manager"],
  ["Joined", "joining_date"], ["Email", "email"],
];

export default function ResultCard({ result }) {
  if (!result) {
    return (
      <div className="card result empty">
        <p className="muted">The verification result will appear here.</p>
      </div>
    );
  }
  const emp = result.employee;
  return (
    <div className={`card result ${result.result.toLowerCase()}`}>
      <div className="result-head">
        <Badge value={result.result} />
        <span>{result.message}</span>
      </div>
      {result.result !== "NO_FACE" && <SimilarityBar value={result.similarity} threshold={result.threshold} />}
      {result.warning && <div className="notice error">{result.warning}</div>}
      {emp && (
        <div className="emp">
          <AuthImage src={`/api/employees/${emp.id}/photo`} alt={emp.name} className="emp-photo" fallback={emp.name.slice(0, 1)} />
          <div className="emp-main">
            <h2>{emp.name}</h2>
            <div className="emp-tags">
              <LevelChip level={emp.access_level} />
              <Badge value={emp.status} />
            </div>
            <dl className="fields">
              {FIELDS.map(([label, key]) => (
                <div key={key}><dt>{label}</dt><dd>{emp[key] || "—"}</dd></div>
              ))}
            </dl>
          </div>
        </div>
      )}
      {emp && (
        <div className="zones">
          <div className="label">Allowed zones</div>
          {result.allowed_zones.length ? (
            <div className="zone-list">{result.allowed_zones.map((z) => <span key={z} className="zone">{z}</span>)}</div>
          ) : (
            <span className="muted">No zones: access blocked.</span>
          )}
        </div>
      )}
      {result.top?.length > 1 && (
        <details className="candidates">
          <summary>Top {result.top.length} guesses</summary>
          <ul>
            {result.top.map((t) => (
              <li key={t.label}>
                <span>{t.name}</span>
                <span className="num">similarity {t.similarity.toFixed(2)} <span className="muted">· classifier {(t.probability * 100).toFixed(0)}%</span></span>
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}
