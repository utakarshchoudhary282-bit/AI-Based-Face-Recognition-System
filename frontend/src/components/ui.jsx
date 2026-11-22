import { useEffect, useState } from "react";
import { api } from "../api.js";

export function PageHeader({ title, subtitle, children }) {
  return (
    <header className="page-header">
      <div>
        <h1>{title}</h1>
        {subtitle && <p className="muted">{subtitle}</p>}
      </div>
      {children && <div className="header-actions">{children}</div>}
    </header>
  );
}

export function Notice({ kind = "info", children, onClose }) {
  if (!children) return null;
  return (
    <div className={`notice ${kind}`} role={kind === "error" ? "alert" : "status"}>
      <span>{children}</span>
      {onClose && <button className="link" onClick={onClose} aria-label="Dismiss">✕</button>}
    </div>
  );
}

const STATUS_CLASS = { Active: "good", "On Leave": "warning", Suspended: "critical", Exited: "neutral",
  MATCH: "good", UNKNOWN: "warning", NO_FACE: "neutral", done: "good", running: "info", failed: "critical" };
const STATUS_ICON = { good: "✓", warning: "!", critical: "✕", neutral: "–", info: "…" };

export function Badge({ value }) {
  const cls = STATUS_CLASS[value] || "neutral";
  return <span className={`badge ${cls}`}><span aria-hidden="true">{STATUS_ICON[cls]}</span>{value}</span>;
}

export function LevelChip({ level }) {
  return <span className={`level level-${level}`}>{level}</span>;
}

/** <img> for API images that need the login token. */
export function AuthImage({ src, alt, className, fallback }) {
  const [url, setUrl] = useState(null);
  useEffect(() => {
    let alive = true;
    let objectUrl;
    setUrl(null);
    if (src) {
      api.blob(src).then((b) => {
        objectUrl = URL.createObjectURL(b);
        if (alive) setUrl(objectUrl);
      }).catch(() => {});
    }
    return () => {
      alive = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [src]);
  if (!url) return <div className={`${className} img-fallback`} aria-label={alt}>{fallback}</div>;
  return <img src={url} alt={alt} className={className} />;
}

export function Spinner({ label = "Loading" }) {
  return <span className="spinner" role="status" aria-label={label} />;
}

export function formatDate(value) {
  if (!value) return "";
  const d = new Date(value.endsWith?.("Z") || value.includes?.("+") ? value : value + "Z");
  return d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}
