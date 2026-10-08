import { useState } from "react";

const EMPTY = { subject: "", description: "", priority: "medium", category: "technical", requester: "", assignee: "" };

export default function TicketModal({ onClose, onCreate }) {
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const set = (key) => (event) => setForm({ ...form, [key]: event.target.value });

  async function submit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      await onCreate(form);
      onClose();
    } catch (err) {
      setError(err.message);
      setSaving(false);
    }
  }

  return (
    <div className="overlay" role="dialog" aria-modal="true" aria-label="Create ticket">
      <form className="modal" onSubmit={submit}>
        <h2>New ticket</h2>
        <label>Subject
          <input required maxLength={200} value={form.subject} onChange={set("subject")} autoFocus />
        </label>
        <label>Description
          <textarea rows={3} maxLength={2000} value={form.description} onChange={set("description")} />
        </label>
        <div className="row">
          <label>Priority
            <select value={form.priority} onChange={set("priority")}>
              {["low", "medium", "high", "urgent"].map((v) => <option key={v}>{v}</option>)}
            </select>
          </label>
          <label>Category
            <select value={form.category} onChange={set("category")}>
              {["billing", "technical", "account", "other"].map((v) => <option key={v}>{v}</option>)}
            </select>
          </label>
        </div>
        <div className="row">
          <label>Requester
            <input value={form.requester} onChange={set("requester")} placeholder="name@example.com" />
          </label>
          <label>Assignee
            <input value={form.assignee} onChange={set("assignee")} />
          </label>
        </div>
        {error && <p className="error">{error}</p>}
        <div className="modal-actions">
          <button type="button" className="btn ghost" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn" disabled={saving}>{saving ? "Saving..." : "Create ticket"}</button>
        </div>
      </form>
    </div>
  );
}
