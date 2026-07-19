const API_BASE = '/api';

export class ApiError extends Error {
  constructor(code, message, details, status) {
    super(message);
    this.code = code;
    this.details = details;
    this.status = status;
  }
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (response.status === 204) return null;

  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('text/csv')) {
    if (!response.ok) {
      const text = await response.text();
      throw new ApiError('export_error', text, null, response.status);
    }
    return response;
  }

  const data = await response.json();
  if (!response.ok) {
    const err = data.error || {};
    throw new ApiError(err.code, err.message, err.details, response.status);
  }
  return data;
}

export const api = {
  health: () => request('/health'),
  getUsers: () => request('/users'),
  getTickets: (params = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== '' && value != null) query.set(key, value);
    });
    const qs = query.toString();
    return request(`/tickets${qs ? `?${qs}` : ''}`);
  },
  getTicket: (id) => request(`/tickets/${id}`),
  createTicket: (body) => request('/tickets', { method: 'POST', body: JSON.stringify(body) }),
  updateTicket: (id, body) => request(`/tickets/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  changeStatus: (id, status) =>
    request(`/tickets/${id}/status`, { method: 'POST', body: JSON.stringify({ status }) }),
  getComments: (id) => request(`/tickets/${id}/comments`),
  addComment: (id, body) =>
    request(`/tickets/${id}/comments`, { method: 'POST', body: JSON.stringify(body) }),
  exportCsv: (createdBy) => request(`/tickets/export?created_by=${createdBy}`),
};
