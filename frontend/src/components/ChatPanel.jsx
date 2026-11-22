import { useEffect, useRef, useState } from "react";
import { api } from "../api.js";
import Markdown from "./Markdown.jsx";
import { Spinner } from "./ui.jsx";

function Sources({ sources, open, highlight }) {
  if (!open) return null;
  return (
    <ol className="sources">
      {sources.map((s) => (
        <li key={s.id} className={highlight === s.id ? "hl" : ""} id={`src-${s.id}`}>
          <div className="src-head">
            <span className="cite static">{s.id}</span>
            <strong>{s.title}</strong>
            {s.section && <span className="muted"> · {s.section}</span>}
            <span className="score" title="How similar this passage is to the question">{s.score == null ? "employee record" : `similarity ${s.score.toFixed(2)}`}</span>
          </div>
          <p>{s.snippet}</p>
        </li>
      ))}
    </ol>
  );
}

function Message({ m }) {
  const [open, setOpen] = useState(false);
  const [hl, setHl] = useState(null);
  if (m.role === "user") return <div className="msg user"><div className="bubble">{m.text}</div></div>;
  if (m.error) return <div className="msg bot"><div className="bubble error">{m.error}</div></div>;
  return (
    <div className="msg bot">
      <div className="bubble">
        <Markdown text={m.answer} onCite={(id) => { setOpen(true); setHl(id); }} />
        <div className="msg-meta">
          <button className="link" onClick={() => setOpen(!open)}>
            {open ? "Hide" : "Show"} {m.sources.length} sources
          </button>
          <span className="muted">
            {m.used_llm ? "Answered by the LLM from the sources below" : m.note}
          </span>
        </div>
        <Sources sources={m.sources} open={open} highlight={hl} />
      </div>
    </div>
  );
}

export default function ChatPanel({ employee, suggestions = [], compact = false }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef(null);

  useEffect(() => { setMessages([]); }, [employee?.id]);
  useEffect(() => { endRef.current?.scrollIntoView({ block: "nearest" }); }, [messages]);

  async function ask(q) {
    const question = (q ?? input).trim();
    if (!question || busy) return;
    setInput("");
    setMessages((ms) => [...ms, { role: "user", text: question }]);
    setBusy(true);
    try {
      const res = await api.post("/api/assistant/ask", { question, employee_id: employee?.id ?? null });
      setMessages((ms) => [...ms, { role: "bot", ...res }]);
    } catch (e) {
      setMessages((ms) => [...ms, { role: "bot", error: e.message }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={`chat ${compact ? "compact" : ""}`}>
      <div className="chat-log" aria-live="polite">
        {messages.length === 0 && (
          <div className="chat-empty">
            <p className="muted">
              {employee
                ? `Ask about ${employee.name}'s access, shift, leave or what to do next. Answers come only from company documents, with sources.`
                : "Ask about company policies: access levels, verification steps, leave, visitors, privacy."}
            </p>
            <div className="suggestions">
              {suggestions.map((s) => (
                <button key={s} className="chip" onClick={() => ask(s)}>{s}</button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => <Message key={i} m={m} />)}
        {busy && <div className="msg bot"><div className="bubble"><Spinner /> Searching documents…</div></div>}
        <div ref={endRef} />
      </div>
      <form className="chat-input" onSubmit={(e) => { e.preventDefault(); ask(); }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={employee ? `Ask about ${employee.name}…` : "Ask a policy question…"}
          aria-label="Question"
          maxLength={1000}
        />
        <button className="btn primary" disabled={busy || !input.trim()}>Ask</button>
      </form>
    </div>
  );
}
