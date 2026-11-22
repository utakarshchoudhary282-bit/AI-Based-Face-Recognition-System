import { useEffect, useState } from "react";
import { api } from "../api.js";
import Markdown from "../components/Markdown.jsx";
import { PageHeader } from "../components/ui.jsx";

export default function Policies() {
  const [docs, setDocs] = useState([]);
  const [open, setOpen] = useState(0);
  useEffect(() => { api.get("/api/policies").then(setDocs).catch(() => {}); }, []);
  return (
    <>
      <PageHeader title="Company policies" subtitle="The 5 documents the RAG assistant searches." />
      <div className="docs-layout">
        <ul className="doc-list card">
          {docs.map((d, i) => (
            <li key={d.name}>
              <button className={open === i ? "doc active" : "doc"} onClick={() => setOpen(i)}>
                <strong>{d.title}</strong>
                <span className="muted small">{d.name}</span>
              </button>
            </li>
          ))}
        </ul>
        <article className="card doc-view">
          {docs[open] ? <Markdown text={docs[open].content} /> : <p className="muted">Loading…</p>}
        </article>
      </div>
    </>
  );
}
