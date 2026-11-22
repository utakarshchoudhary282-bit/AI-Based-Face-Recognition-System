import { useEffect, useRef, useState } from "react";
import { api, filesForm } from "../api.js";
import { AuthImage, Badge, LevelChip, Notice, PageHeader, Spinner } from "../components/ui.jsx";

const EMPTY = { name: "", label: "", department: "", designation: "", access_level: "L1", email: "", phone: "",
  office_location: "", shift: "General (9:30-18:30)", manager: "", joining_date: "", status: "Active", notes: "" };
const TEXT_FIELDS = [["name", "Full name *"], ["department", "Department"], ["designation", "Designation"],
  ["manager", "Reporting manager"], ["email", "Email"], ["phone", "Phone"], ["office_location", "Office location"],
  ["joining_date", "Joining date"]];
const SHIFTS = ["General (9:30-18:30)", "Morning (7:00-16:00)", "Evening (14:00-23:00)"];

function EmployeeForm({ initial, onSaved, onCancel }) {
  const editing = Boolean(initial?.id);
  const [form, setForm] = useState(editing ? { ...EMPTY, ...initial } : EMPTY);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function save(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const body = { ...form };
      ["id", "has_photo", "face_images", "employee_code"].forEach((k) => delete body[k]);
      if (editing) delete body.label;
      else if (!body.label) delete body.label;
      const saved = editing ? await api.patch(`/api/employees/${initial.id}`, body) : await api.post("/api/employees", body);
      onSaved(saved);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="card form-grid" onSubmit={save}>
      <h2 className="section-title span-2">{editing ? `Edit ${initial.name}` : "Add employee"}</h2>
      {TEXT_FIELDS.map(([k, label]) => (
        <label key={k}>{label}
          <input type={k === "joining_date" ? "date" : k === "email" ? "email" : "text"} value={form[k] || ""}
            onChange={set(k)} required={k === "name"} />
        </label>
      ))}
      {!editing && (
        <label>Folder / model label
          <input value={form.label} onChange={set("label")} placeholder="auto from name, e.g. harshal" />
        </label>
      )}
      <label>Access level
        <select value={form.access_level} onChange={set("access_level")}>
          {["L1", "L2", "L3", "L4"].map((l) => <option key={l}>{l}</option>)}
        </select>
      </label>
      <label>Status
        <select value={form.status} onChange={set("status")}>
          {["Active", "On Leave", "Suspended", "Exited"].map((s) => <option key={s}>{s}</option>)}
        </select>
      </label>
      <label>Shift
        <select value={form.shift} onChange={set("shift")}>
          {SHIFTS.map((s) => <option key={s}>{s}</option>)}
        </select>
      </label>
      <label className="span-2">Notes
        <textarea rows={2} value={form.notes || ""} onChange={set("notes")} />
      </label>
      <Notice kind="error">{error}</Notice>
      <div className="span-2 row-end">
        <button type="button" className="btn ghost" onClick={onCancel}>Cancel</button>
        <button className="btn primary" disabled={busy}>{busy ? <Spinner /> : null} Save</button>
      </div>
    </form>
  );
}

function UploadButtons({ emp, onDone }) {
  const folderRef = useRef(null);
  const filesRef = useRef(null);
  const [busy, setBusy] = useState(false);

  async function upload(fileList) {
    const files = [...fileList].filter((f) => f.type.startsWith("image/"));
    if (!files.length) return onDone({ error: "No images found in that selection." });
    setBusy(true);
    try {
      const report = await api.upload(`/api/employees/${emp.id}/images`, filesForm("files", files));
      onDone({ report, emp });
    } catch (e) {
      onDone({ error: e.message });
    } finally {
      setBusy(false);
      folderRef.current.value = "";
      filesRef.current.value = "";
    }
  }

  return (
    <div className="row-actions">
      <input ref={folderRef} type="file" hidden webkitdirectory="" directory="" multiple onChange={(e) => upload(e.target.files)} />
      <input ref={filesRef} type="file" hidden accept="image/*" multiple onChange={(e) => upload(e.target.files)} />
      <button className="btn small" disabled={busy} onClick={() => folderRef.current.click()}>
        {busy ? <Spinner /> : "Upload folder"}
      </button>
      <button className="btn small ghost" disabled={busy} onClick={() => filesRef.current.click()}>Photos</button>
    </div>
  );
}

export default function Employees() {
  const [rows, setRows] = useState(null);
  const [editing, setEditing] = useState(null);
  const [notice, setNotice] = useState(null);
  const [query, setQuery] = useState("");

  const load = () => api.get("/api/employees").then(setRows).catch((e) => setNotice({ kind: "error", text: e.message }));
  useEffect(() => { load(); }, []);

  async function remove(emp) {
    if (!window.confirm(`Delete ${emp.name}? Their face photos are deleted too (privacy policy). Retrain the model afterwards.`)) return;
    try {
      await api.del(`/api/employees/${emp.id}`);
      setNotice({ kind: "info", text: `${emp.name} deleted. Retrain the model to remove them from recognition.` });
      load();
    } catch (e) {
      setNotice({ kind: "error", text: e.message });
    }
  }

  function uploaded({ report, emp, error }) {
    if (error) return setNotice({ kind: "error", text: error });
    setNotice({
      kind: report.skipped.length ? "warning" : "info",
      text: `${emp.name}: ${report.saved} faces saved, ${report.skipped.length} photos without a face skipped ` +
        `(${report.total_faces} in total).` + (report.total_faces >= 5 ? " Ready for training." : " Add more photos: 5+ needed."),
    });
    load();
  }

  const shown = (rows || []).filter((r) => `${r.name} ${r.employee_code} ${r.department} ${r.label}`.toLowerCase().includes(query.toLowerCase()));
  return (
    <>
      <PageHeader title="Employees" subtitle="People the model can recognise. Upload a folder of face photos for each person, then train.">
        <input className="search" placeholder="Search…" value={query} onChange={(e) => setQuery(e.target.value)} aria-label="Search employees" />
        <button className="btn primary" onClick={() => setEditing({})}>Add employee</button>
      </PageHeader>
      {notice && <Notice kind={notice.kind} onClose={() => setNotice(null)}>{notice.text}</Notice>}
      {editing && (
        <EmployeeForm initial={editing} onCancel={() => setEditing(null)}
          onSaved={(e) => { setEditing(null); setNotice({ kind: "info", text: `${e.name} saved.` }); load(); }} />
      )}
      <div className="card table-card">
        {!rows ? <Spinner /> : rows.length === 0 ? (
          <p className="muted pad">No employees yet. Add one, or upload a zip with a folder per person on the Enrol & Train page.</p>
        ) : (
          <table>
            <thead>
              <tr><th></th><th>Name</th><th>Code</th><th>Department</th><th>Level</th><th>Status</th><th className="num">Face images</th><th>Upload</th><th></th></tr>
            </thead>
            <tbody>
              {shown.map((e) => (
                <tr key={e.id}>
                  <td><AuthImage src={e.has_photo ? `/api/employees/${e.id}/photo` : null} alt="" className="thumb" fallback={e.name.slice(0, 1)} /></td>
                  <td><strong>{e.name}</strong><div className="muted small">{e.designation || e.label}</div></td>
                  <td>{e.employee_code}</td>
                  <td>{e.department || "—"}</td>
                  <td><LevelChip level={e.access_level} /></td>
                  <td><Badge value={e.status} /></td>
                  <td className="num"><span className={e.face_images >= 10 ? "" : "warn-text"}>{e.face_images}</span></td>
                  <td><UploadButtons emp={e} onDone={uploaded} /></td>
                  <td className="row-actions">
                    <button className="btn small ghost" onClick={() => setEditing(e)}>Edit</button>
                    <button className="btn small danger" onClick={() => remove(e)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
