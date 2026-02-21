import { useState, useRef, useCallback } from "react";
import { Sparkles, Loader, Send } from "lucide-react";
import toast from "react-hot-toast";
import { ticketsApi } from "../api/tickets";

const CATEGORIES = ["billing", "technical", "account", "general"];
const PRIORITIES = ["low", "medium", "high", "critical"];

const INITIAL_FORM = {
  title: "",
  description: "",
  category: "general",
  priority: "medium",
};

export default function TicketForm({ onTicketCreated }) {
  const [form, setForm] = useState(INITIAL_FORM);
  const [classifying, setClassifying] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [aiSuggestion, setAiSuggestion] = useState(null);
  const debounceRef = useRef(null);

  const handleChange = useCallback(
    (e) => {
      const { name, value } = e.target;
      setForm((prev) => ({ ...prev, [name]: value }));

      if (name === "description" && value.trim().length >= 20) {
        clearTimeout(debounceRef.current);
        debounceRef.current = setTimeout(() => {
          runClassify(value.trim());
        }, 800);
      }
    },
    []
  );

  const runClassify = async (description) => {
    setClassifying(true);
    try {
      const { data } = await ticketsApi.classify(description);
      setAiSuggestion(data);
      setForm((prev) => ({
        ...prev,
        category: data.suggested_category,
        priority: data.suggested_priority,
      }));
    } catch {
      // Silently fail — the user can still select manually
    } finally {
      setClassifying(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.title.trim() || !form.description.trim()) {
      toast.error("Title and description are required.");
      return;
    }
    setSubmitting(true);
    try {
      const { data } = await ticketsApi.create(form);
      toast.success("Ticket submitted!");
      setForm(INITIAL_FORM);
      setAiSuggestion(null);
      onTicketCreated(data);
    } catch (err) {
      const msg =
        err?.response?.data?.detail ||
        Object.values(err?.response?.data || {})[0]?.[0] ||
        "Failed to submit ticket.";
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="card">
      <div className="page-header">
        <div className="page-title">Submit a Ticket</div>
        <div className="page-subtitle">Describe your issue and our AI will categorize it for you.</div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">Title *</label>
          <input
            className="form-input"
            name="title"
            value={form.title}
            onChange={handleChange}
            placeholder="Short summary of the issue"
            maxLength={200}
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label">Description *</label>
          <textarea
            className="form-textarea"
            name="description"
            value={form.description}
            onChange={handleChange}
            placeholder="Describe your problem in detail... (AI will auto-suggest category & priority)"
            required
          />
          {classifying && (
            <div className="ai-suggestion">
              <Loader size={13} className="spinner" />
              AI is analyzing your description…
            </div>
          )}
          {!classifying && aiSuggestion && (
            <div className="ai-suggestion">
              <Sparkles size={13} />
              AI suggested: <strong>{aiSuggestion.suggested_category}</strong> · <strong>{aiSuggestion.suggested_priority}</strong> priority — override below if needed.
            </div>
          )}
        </div>

        <div className="form-row">
          <div className="form-group">
            <label className="form-label">Category</label>
            <select
              className="form-select"
              name="category"
              value={form.category}
              onChange={handleChange}
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c.charAt(0).toUpperCase() + c.slice(1)}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Priority</label>
            <select
              className="form-select"
              name="priority"
              value={form.priority}
              onChange={handleChange}
            >
              {PRIORITIES.map((p) => (
                <option key={p} value={p}>
                  {p.charAt(0).toUpperCase() + p.slice(1)}
                </option>
              ))}
            </select>
          </div>
        </div>

        <button
          type="submit"
          className="btn btn-primary btn-full"
          disabled={submitting}
        >
          {submitting ? (
            <><Loader size={16} className="spinner" /> Submitting…</>
          ) : (
            <><Send size={16} /> Submit Ticket</>
          )}
        </button>
      </form>
    </div>
  );
}
