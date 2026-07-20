import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import { PRIORITIES, STATUSES } from '../constants';
import { useUser } from '../context/UserContext';
import { ErrorBanner, formatApiError } from '../components/ErrorBanner';

export default function TicketListPage() {
  const { currentUser } = useUser();
  const [tickets, setTickets] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({ q: '', status: '', priority: '' });

  const loadTickets = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getTickets(filters);
      setTickets(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTickets();
  }, [filters]);

  const handleExport = async () => {
    if (!currentUser?.id) return;
    try {
      const response = await api.exportCsv();
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `tickets_user_${currentUser.id}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(formatApiError(err));
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Support Tickets</h1>
          <p className="muted">{total} ticket{total !== 1 ? 's' : ''}</p>
        </div>
        <div className="actions">
          <button type="button" className="btn btn-secondary" onClick={handleExport}>
            Export my tickets (CSV)
          </button>
          <Link to="/tickets/new" className="btn btn-primary">
            New Ticket
          </Link>
        </div>
      </div>

      <ErrorBanner message={error} onDismiss={() => setError(null)} />

      <div className="filters card">
        <input
          type="search"
          placeholder="Search title or description..."
          value={filters.q}
          onChange={(e) => setFilters((f) => ({ ...f, q: e.target.value }))}
        />
        <select
          value={filters.status}
          onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
        >
          <option value="">All statuses</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <select
          value={filters.priority}
          onChange={(e) => setFilters((f) => ({ ...f, priority: e.target.value }))}
        >
          <option value="">All priorities</option>
          {PRIORITIES.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
      </div>

      <div className="card">
        {loading ? (
          <p className="muted">Loading tickets...</p>
        ) : tickets.length === 0 ? (
          <p className="muted">No tickets found.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Assignee</th>
                <th>Created By</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map((ticket) => (
                <tr key={ticket.id}>
                  <td>{ticket.id}</td>
                  <td>
                    <Link to={`/tickets/${ticket.id}`}>{ticket.title}</Link>
                  </td>
                  <td>
                    <span className={`badge priority-${ticket.priority.toLowerCase()}`}>
                      {ticket.priority}
                    </span>
                  </td>
                  <td>
                    <span className={`badge status-${ticket.status.replace(/\s/g, '-').toLowerCase()}`}>
                      {ticket.status}
                    </span>
                  </td>
                  <td>{ticket.assignee?.name || '—'}</td>
                  <td>{ticket.creator?.name || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
