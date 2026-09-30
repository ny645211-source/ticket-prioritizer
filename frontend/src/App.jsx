import { useCallback, useEffect, useState } from "react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
const EMPTY = { customer: "", plan: "free", subject: "", body: "" };

export default function App() {
  const [tickets, setTickets] = useState([]);
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState("");
  const [openId, setOpenId] = useState(null);

  const load = useCallback(async () => {
    try {
      const res = await fetch(`${API}/tickets?status=open`);
      if (!res.ok) throw new Error();
      setTickets(await res.json());
      setError("");
    } catch {
      setError("Can't reach the API. Check that the backend is running on port 8000.");
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, [load]);

  async function submit(e) {
    e.preventDefault();
    const res = await fetch(`${API}/tickets`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    if (!res.ok) return setError("Ticket not saved. Fill in every field.");
    setForm(EMPTY);
    load();
  }

  async function resolve(id) {
    await fetch(`${API}/tickets/${id}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "resolved" }),
    });
    load();
  }

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  return (
    <main className="shell">
      <section className="queue">
        <h1>Open tickets, most urgent first</h1>
        {error && <p className="error" role="alert">{error}</p>}
        {!error && tickets.length === 0 && <p className="empty">Queue is clear. New tickets appear here ranked by urgency.</p>}
        <ul>
          {tickets.map((t) => (
            <li key={t.id} className={`ticket ${t.priority}`}>
              <button className="row" onClick={() => setOpenId(openId === t.id ? null : t.id)} aria-expanded={openId === t.id}>
                <span className="badge">{t.priority}</span>
                <span className="main">
                  <strong>{t.subject}</strong>
                  <small>{t.customer} · {t.plan} · {t.category?.replace("_", " ")}</small>
                </span>
                <span className="score">{Math.round(t.score)}</span>
              </button>
              {openId === t.id && (
                <div className="detail">
                  <p>{t.body}</p>
                  <p className="why">Why this rank: {t.reasons}</p>
                  <button className="primary" onClick={() => resolve(t.id)}>Mark resolved</button>
                </div>
              )}
            </li>
          ))}
        </ul>
      </section>

      <form className="new" onSubmit={submit}>
        <h2>Add a ticket</h2>
        <label>Customer<input value={form.customer} onChange={set("customer")} required /></label>
        <label>Plan
          <select value={form.plan} onChange={set("plan")}>
            <option value="free">Free</option><option value="pro">Pro</option><option value="enterprise">Enterprise</option>
          </select>
        </label>
        <label>Subject<input value={form.subject} onChange={set("subject")} required minLength={3} /></label>
        <label>Message<textarea rows={5} value={form.body} onChange={set("body")} required minLength={3} /></label>
        <button className="primary" type="submit">Score and add</button>
      </form>
    </main>
  );
}
