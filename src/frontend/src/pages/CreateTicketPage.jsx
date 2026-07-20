import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { PRIORITIES } from '../constants';
import { useUser } from '../context/UserContext';
import { ErrorBanner, FieldError, formatApiError } from '../components/ErrorBanner';

export default function CreateTicketPage() {
  const navigate = useNavigate();
  const { users } = useUser();
  const [form, setForm] = useState({
    title: '',
    description: '',
    priority: 'Medium',
    assigned_to: '',
  });
  const [fieldErrors, setFieldErrors] = useState({});
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setFieldErrors({});

    try {
      const ticket = await api.createTicket({
        title: form.title,
        description: form.description,
        priority: form.priority,
        assigned_to: form.assigned_to ? Number(form.assigned_to) : null,
      });
      navigate(`/tickets/${ticket.id}`);
    } catch (err) {
      if (err.status === 422 && Array.isArray(err.details)) {
        const errors = {};
        err.details.forEach((d) => {
          const field = d.loc?.[d.loc.length - 1];
          if (field) errors[field] = d.msg;
        });
        setFieldErrors(errors);
      } else {
        setError(formatApiError(err));
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <Link to="/" className="back-link">← Back to list</Link>
          <h1>Create Ticket</h1>
        </div>
      </div>

      <ErrorBanner message={error} onDismiss={() => setError(null)} />

      <form className="card form" onSubmit={handleSubmit}>
        <label>
          Title *
          <input
            value={form.title}
            onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
            placeholder="Brief summary (3–120 characters)"
          />
          <FieldError error={fieldErrors.title} />
        </label>

        <label>
          Description
          <textarea
            rows={5}
            value={form.description}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
            placeholder="Detailed description"
          />
          <FieldError error={fieldErrors.description} />
        </label>

        <label>
          Priority
          <select
            value={form.priority}
            onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}
          >
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </label>

        <label>
          Assignee (optional)
          <select
            value={form.assigned_to}
            onChange={(e) => setForm((f) => ({ ...f, assigned_to: e.target.value }))}
          >
            <option value="">Unassigned</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>{u.name}</option>
            ))}
          </select>
        </label>

        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? 'Creating...' : 'Create Ticket'}
          </button>
        </div>
      </form>
    </div>
  );
}
