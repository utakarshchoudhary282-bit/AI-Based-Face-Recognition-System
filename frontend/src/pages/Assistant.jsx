import { useEffect, useState } from "react";
import { api } from "../api.js";
import { useAuth } from "../App.jsx";
import ChatPanel from "../components/ChatPanel.jsx";
import { PageHeader } from "../components/ui.jsx";

export default function Assistant() {
  const { user } = useAuth();
  const [status, setStatus] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [selected, setSelected] = useState("");

  useEffect(() => {
    api.get("/api/assistant/status").then(setStatus).catch(() => {});
    if (user.role === "admin") api.get("/api/employees").then(setEmployees).catch(() => {});
  }, [user.role]);

  const employee = employees.find((e) => String(e.id) === selected) || null;
  return (
    <>
      <PageHeader title="Policy assistant (RAG)"
        subtitle="It searches the company policies, then the LLM answers only from what it found, with numbered sources." />
      {status && (
        <div className="pipeline card">
          <div><span className="label">1. Search</span>FAISS over {status.policies} policy documents, top 4 passages</div>
          <div><span className="label">2. Context</span>The verified employee's record, if one is selected</div>
          <div><span className="label">3. Answer</span>{status.llm}</div>
        </div>
      )}
      <div className="card">
        {user.role === "admin" && (
          <label className="inline">
            Ask about a specific employee (optional)
            <select value={selected} onChange={(e) => setSelected(e.target.value)}>
              <option value="">No employee: general policy question</option>
              {employees.map((e) => <option key={e.id} value={e.id}>{e.name} ({e.access_level}, {e.status})</option>)}
            </select>
          </label>
        )}
        <ChatPanel employee={employee} suggestions={employee ? [
          `Can ${employee.name} enter the R&D lab?`,
          `Is ${employee.name} allowed into the office today?`,
          `How can ${employee.name} get L4 access?`,
        ] : [
          "What does access level L3 allow?",
          "What should security do if the result is Unknown?",
          "How many sick leaves do employees get?",
          "How long are verification logs kept?",
        ]} />
      </div>
    </>
  );
}
