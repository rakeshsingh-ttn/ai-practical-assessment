import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../api/client';
import {
  ALLOWED_TRANSITIONS,
  COMMENT_ALLOWED_STATUSES,
  EDITABLE_STATUSES,
  PRIORITIES,
  STATUS_CHANGE_ROLES,
} from '../constants';
import { useUser } from '../context/UserContext';
import { ErrorBanner, FieldError, formatApiError } from '../components/ErrorBanner';

export default function TicketDetailPage() {
  const { id } = useParams();
  const { users, currentUser } = useUser();
  const [ticket, setTicket] = useState(null);
  const [comments, setComments] = useState([]);
  const [editForm, setEditForm] = useState(null);
  const [commentText, setCommentText] = useState('');
  const [error, setError] = useState(null);
  const [fieldErrors, setFieldErrors] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const isEditable = ticket && EDITABLE_STATUSES.includes(ticket.status);
  const canEdit =
    isEditable &&
    (currentUser?.role !== 'Requester' || ticket?.created_by === currentUser?.id);
  const canComment = ticket && COMMENT_ALLOWED_STATUSES.includes(ticket.status);
  const canCommentOnTicket =
    canComment &&
    (currentUser?.role !== 'Requester' || ticket?.created_by === currentUser?.id);
  const transitions = ticket ? ALLOWED_TRANSITIONS[ticket.status] || [] : [];
  const canChangeStatus =
    transitions.length > 0 && STATUS_CHANGE_ROLES.includes(currentUser?.role);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [ticketData, commentsData] = await Promise.all([
        api.getTicket(id),
        api.getComments(id),
      ]);
      setTicket(ticketData);
      setComments(commentsData);
      setEditForm({
        title: ticketData.title,
        description: ticketData.description,
        priority: ticketData.priority,
        assigned_to: ticketData.assigned_to || '',
      });
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [id]);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setFieldErrors({});
    try {
      const updated = await api.updateTicket(id, {
        title: editForm.title,
        description: editForm.description,
        priority: editForm.priority,
        assigned_to: editForm.assigned_to ? Number(editForm.assigned_to) : null,
      });
      setTicket(updated);
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
      setSaving(false);
    }
  };

  const handleStatusChange = async (status) => {
    setError(null);
    try {
      const updated = await api.changeStatus(id, status);
      setTicket(updated);
      await load();
    } catch (err) {
      setError(formatApiError(err));
    }
  };

  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!commentText.trim()) return;
    setError(null);
    try {
      await api.addComment(id, { message: commentText });
      setCommentText('');
      const commentsData = await api.getComments(id);
      setComments(commentsData);
    } catch (err) {
      setError(formatApiError(err));
    }
  };

  if (loading) {
    return <div className="page"><p className="muted">Loading ticket...</p></div>;
  }

  if (!ticket) {
    return (
      <div className="page">
        <ErrorBanner message={error || 'Ticket not found'} />
        <Link to="/">← Back to list</Link>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <Link to="/" className="back-link">← Back to list</Link>
          <h1>#{ticket.id} — {ticket.title}</h1>
          <div className="meta">
            <span className={`badge status-${ticket.status.replace(/\s/g, '-').toLowerCase()}`}>
              {ticket.status}
            </span>
            <span className={`badge priority-${ticket.priority.toLowerCase()}`}>
              {ticket.priority}
            </span>
            <span className="muted">
              Created by {ticket.creator?.name} · {new Date(ticket.created_at).toLocaleString()}
            </span>
          </div>
        </div>
      </div>

      <ErrorBanner message={error} onDismiss={() => setError(null)} />

      {canChangeStatus && (
        <div className="card status-actions">
          <h2>Status Actions</h2>
          <div className="btn-group">
            {transitions.map((status) => (
              <button
                key={status}
                type="button"
                className="btn btn-secondary"
                onClick={() => handleStatusChange(status)}
              >
                Move to {status}
              </button>
            ))}
          </div>
        </div>
      )}

      {!canEdit && (
        <div className="card info-banner">
          This ticket is read-only
          {ticket.status !== 'Open' && ticket.status !== 'In Progress'
            ? <> because it is in <strong>{ticket.status}</strong> status</>
            : currentUser?.role === 'Requester' && ticket.created_by !== currentUser?.id
              ? <> because you can only edit your own tickets</>
              : <> because it is in <strong>{ticket.status}</strong> status</>}
          .
        </div>
      )}

      <form className="card form" onSubmit={handleSave}>
        <h2>Details</h2>
        <label>
          Title
          <input
            value={editForm.title}
            disabled={!canEdit}
            onChange={(e) => setEditForm((f) => ({ ...f, title: e.target.value }))}
          />
          <FieldError error={fieldErrors.title} />
        </label>
        <label>
          Description
          <textarea
            rows={6}
            disabled={!canEdit}
            value={editForm.description}
            onChange={(e) => setEditForm((f) => ({ ...f, description: e.target.value }))}
          />
        </label>
        <label>
          Priority
          <select
            disabled={!canEdit}
            value={editForm.priority}
            onChange={(e) => setEditForm((f) => ({ ...f, priority: e.target.value }))}
          >
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </label>
        <label>
          Assignee
          <select
            disabled={!canEdit}
            value={editForm.assigned_to}
            onChange={(e) => setEditForm((f) => ({ ...f, assigned_to: e.target.value }))}
          >
            <option value="">Unassigned</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>{u.name}</option>
            ))}
          </select>
        </label>
        {canEdit && (
          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        )}
      </form>

      <div className="card">
        <h2>Comments</h2>
        {comments.length === 0 ? (
          <p className="muted">No comments yet.</p>
        ) : (
          <ul className="comment-list">
            {comments.map((c) => (
              <li key={c.id}>
                <div className="comment-meta">
                  <strong>{c.author?.name || 'User'}</strong>
                  <span className="muted">{new Date(c.created_at).toLocaleString()}</span>
                </div>
                <p>{c.message}</p>
              </li>
            ))}
          </ul>
        )}

        {canCommentOnTicket ? (
          <form className="comment-form" onSubmit={handleAddComment}>
            <textarea
              rows={3}
              placeholder="Add a comment..."
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
            />
            <button type="submit" className="btn btn-primary">Add Comment</button>
          </form>
        ) : (
          <p className="muted">
            {canComment
              ? <>Comments are only available on your own tickets.</>
              : <>Comments are disabled for tickets in <strong>{ticket.status}</strong> status.</>}
          </p>
        )}
      </div>
    </div>
  );
}
