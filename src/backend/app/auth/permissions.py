from src.backend.app.exceptions import ForbiddenError
from src.backend.app.models.entities import Ticket, User, UserRole

STATUS_CHANGE_ROLES = frozenset({UserRole.ADMIN, UserRole.AGENT, UserRole.MANAGER})


def require_status_change_role(actor: User) -> None:
    if actor.role not in STATUS_CHANGE_ROLES:
        raise ForbiddenError("Only Admin, Agent, or Manager can change ticket status")


def require_ticket_owner(actor: User, ticket: Ticket) -> None:
    if actor.role == UserRole.REQUESTER and ticket.created_by != actor.id:
        raise ForbiddenError("Requesters can only modify their own tickets")
