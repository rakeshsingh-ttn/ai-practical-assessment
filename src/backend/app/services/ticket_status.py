from src.backend.app.models.entities import Ticket, TicketStatus

ALLOWED_TRANSITIONS: dict[TicketStatus, set[TicketStatus]] = {
    TicketStatus.OPEN: {TicketStatus.IN_PROGRESS, TicketStatus.CANCELLED},
    TicketStatus.IN_PROGRESS: {TicketStatus.RESOLVED, TicketStatus.CANCELLED},
    TicketStatus.RESOLVED: {TicketStatus.CLOSED},
    TicketStatus.CLOSED: set(),
    TicketStatus.CANCELLED: set(),
}

EDITABLE_STATUSES = {TicketStatus.OPEN, TicketStatus.IN_PROGRESS}
COMMENT_ALLOWED_STATUSES = {
    TicketStatus.OPEN,
    TicketStatus.IN_PROGRESS,
    TicketStatus.RESOLVED,
}


def can_transition(current: TicketStatus, target: TicketStatus) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, set())


def transition(ticket: Ticket, target: TicketStatus) -> Ticket:
    from src.backend.app.exceptions import InvalidTransitionError

    current = ticket.status
    if not can_transition(current, target):
        allowed = [s.value for s in sorted(ALLOWED_TRANSITIONS.get(current, set()), key=lambda x: x.value)]
        raise InvalidTransitionError(current.value, target.value, allowed)
    ticket.status = target
    return ticket
