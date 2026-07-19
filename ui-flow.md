# UI Flow

Three screens: **Ticket List**, **Ticket Detail**, and **Create Ticket**. All share a persistent header with the **Acting as** user selector.

---

## Global: Header

```
┌──────────────────────────────────────────────────────────────┐
│  TicketDesk          Acting as: [ Alice Admin (Admin)  ▼ ]   │
└──────────────────────────────────────────────────────────────┘
```

- Dropdown populated from `GET /api/users`.
- Selection persisted in `UserContext` for the session.
- Drives `created_by` on creates/comments and CSV export scope.

---

## Screen 1: Ticket List (`/`)

### Layout

```
┌──────────────────────────────────────────────────────────────┐
│  Support Tickets                    [Export CSV] [New Ticket]  │
│  12 tickets                                                  │
├──────────────────────────────────────────────────────────────┤
│  [ Search title or description... ] [Status ▼] [Priority ▼]  │
├──────────────────────────────────────────────────────────────┤
│  ID │ Title              │ Priority │ Status    │ Assignee │ Created by │
│  1  │ Cannot login       │ High     │ Open      │ Bob      │ Dana       │
│  2  │ Printer offline    │ Low      │ Resolved  │ —        │ Alice      │
│  ...                                                         │
└──────────────────────────────────────────────────────────────┘
```

### User flows

| Action | Flow |
|--------|------|
| **Load page** | `GET /api/tickets` → render table; show count |
| **Search** | Type in search box → debounced/filter on change → `GET /api/tickets?q=...` (case-insensitive title + description) |
| **Filter status** | Select status → `GET /api/tickets?status=Open` |
| **Filter priority** | Select priority → `GET /api/tickets?priority=High` |
| **Combined filters** | AND logic — `?q=login&status=Open&priority=High` |
| **Click row / title** | Navigate to `/tickets/{id}` |
| **New Ticket** | Navigate to `/tickets/new` |
| **Export my tickets** | `GET /api/tickets/export?created_by={currentUserId}` → browser download CSV |

### Error states

| Condition | UI behaviour |
|-----------|--------------|
| List load fails (404, 500) | Red **ErrorBanner** at top: server `message`; dismissible |
| Export fails | Same banner with export error message |

---

## Screen 2: Ticket Detail (`/tickets/:id`)

### Layout (Open / In Progress — editable)

```
┌──────────────────────────────────────────────────────────────┐
│  ← Back to list                                              │
│  #1  Cannot login to portal          [ Open ]  [ High ]      │
├──────────────────────────────────────────────────────────────┤
│  Status actions:  [ Start Progress ]  [ Cancel ]             │
├──────────────────────────────────────────────────────────────┤
│  Title:    [ Cannot login to portal        ]                 │
│  Desc:     [ User reports 401...           ]                 │
│  Priority: [ High ▼ ]   Assignee: [ Bob Agent ▼ ]            │
│                              [ Save changes ]                │
├──────────────────────────────────────────────────────────────┤
│  Comments                                                    │
│  ┌ Bob Agent · 11:00 ─────────────────────────────────┐    │
│  │ Investigating the auth logs now.                     │    │
│  └──────────────────────────────────────────────────────┘    │
│  [ Add a comment...                    ] [ Post ]            │
└──────────────────────────────────────────────────────────────┘
```

### Layout (Closed / Cancelled — read-only)

```
├──────────────────────────────────────────────────────────────┤
│  ⚠ This ticket is Closed. Editing and commenting are disabled.│
├──────────────────────────────────────────────────────────────┤
│  Title:    Cannot login to portal        (read-only)         │
│  ...                                                         │
│  Comments (read-only thread — existing comments still shown) │
└──────────────────────────────────────────────────────────────┘
```

### Status action buttons

Rendered from `ALLOWED_TRANSITIONS[currentStatus]` — **only valid next states**:

| Current status | Buttons shown |
|----------------|---------------|
| Open | Start Progress, Cancel |
| In Progress | Mark Resolved, Cancel |
| Resolved | Close |
| Closed | *(none)* |
| Cancelled | *(none)* |

Click → `POST /api/tickets/{id}/status` → refresh ticket.

### User flows

| Action | Flow |
|--------|------|
| **Load** | `GET /api/tickets/{id}` + `GET /api/tickets/{id}/comments` in parallel |
| **Save edits** | `PATCH /api/tickets/{id}` (only if Open/In Progress) → update local state |
| **Status change** | `POST /api/tickets/{id}/status` → reload ticket + comments |
| **Add comment** | `POST /api/tickets/{id}/comments` with `created_by: currentUserId` → append to thread |

### Edit / comment availability

| Status | Edit form | Comment form |
|--------|-----------|--------------|
| Open | Enabled | Enabled |
| In Progress | Enabled | Enabled |
| Resolved | Disabled (read-only fields) | Enabled |
| Closed | Disabled + explanation | Disabled + explanation |
| Cancelled | Disabled + explanation | Disabled + explanation |

### Error states

| Condition | UI behaviour |
|-----------|--------------|
| Ticket not found (404) | **ErrorBanner**: "Ticket not found" |
| Validation failure on save (422) | Inline **FieldError** under title/description/etc. |
| Edit on read-only ticket (409) | **ErrorBanner**: "Ticket cannot be edited in 'Resolved' status." |
| Invalid transition (409) | **ErrorBanner** with friendly server message, e.g. *"Cannot transition from 'Open' to 'Resolved'. Allowed transitions: In Progress, Cancelled."* |
| Comment on closed ticket (409) | **ErrorBanner**: "Comments are not allowed on tickets in 'Closed' status." |
| Generic API failure | **ErrorBanner** with server `message` |

---

## Screen 3: Create Ticket (`/tickets/new`)

### Layout

```
┌──────────────────────────────────────────────────────────────┐
│  ← Back to list                                              │
│  Create Ticket                                               │
├──────────────────────────────────────────────────────────────┤
│  Title *       [ Brief summary (3–120 characters)     ]      │
│                ⚠ String should have at least 3 characters     │  ← inline 422
│  Description   [ Detailed description                 ]      │
│  Priority      [ Medium ▼ ]                                  │
│  Assignee      [ Unassigned ▼ ]  (optional)                  │
│                              [ Create Ticket ]               │
└──────────────────────────────────────────────────────────────┘
```

### User flow

1. User fills form; `created_by` set from acting-as selector (not shown in form).
2. Submit → `POST /api/tickets`.
3. **Success (201)** → navigate to `/tickets/{id}` detail view.
4. **Validation failure (422)** → inline field errors under each invalid field; form stays open.
5. **User not found (404)** → **ErrorBanner** (should not occur with valid acting-as selection).
6. **Other errors** → **ErrorBanner**.

### Error states

| Condition | UI behaviour |
|-----------|--------------|
| Title too short (422) | Inline error under Title field |
| Invalid priority (422) | Inline error under Priority field |
| Server/network error | **ErrorBanner** at top |

---

## Error State Summary

| HTTP | Where | UI component |
|------|-------|--------------|
| **422** | Create form, edit form | Inline `FieldError` per field |
| **404** | Any screen | `ErrorBanner` |
| **409** | Status change, edit, comment | `ErrorBanner` with server message (transition errors are user-friendly) |
| **500** | Any screen | `ErrorBanner` |

All errors parsed from `{"error": {"code", "message", "details"}}` via `api/client.js` → `ApiError`.
