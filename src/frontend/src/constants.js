export const ALLOWED_TRANSITIONS = {
  Open: ['In Progress', 'Cancelled'],
  'In Progress': ['Resolved', 'Cancelled'],
  Resolved: ['Closed'],
  Closed: [],
  Cancelled: [],
};

export const EDITABLE_STATUSES = ['Open', 'In Progress'];
export const COMMENT_ALLOWED_STATUSES = ['Open', 'In Progress', 'Resolved'];

export const PRIORITIES = ['Low', 'Medium', 'High'];
export const STATUSES = ['Open', 'In Progress', 'Resolved', 'Closed', 'Cancelled'];
