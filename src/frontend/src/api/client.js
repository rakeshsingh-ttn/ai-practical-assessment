const API_BASE = '/api';
const TOKEN_KEY = 'authToken';

let unauthorizedHandler = () => {};

export function setUnauthorizedHandler(handler) {
  unauthorizedHandler = handler;
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  constructor(code, message, details, status) {
    super(message);
    this.code = code;
    this.details = details;
    this.status = status;
  }
}

async function request(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    });
  } catch {
    throw new ApiError('network_error', 'Unable to reach the server. Check your connection.', null, 0);
  }

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
    if (response.status === 401 && token) {
      clearToken();
      unauthorizedHandler();
    }
    const err = data.error || {};
    throw new ApiError(err.code, err.message, err.details, response.status);
  }
  return data;
}

export const api = {
  login: (email, password) =>
    request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  me: () => request('/auth/me'),
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
  exportCsv: () => request('/tickets/export'),
};
