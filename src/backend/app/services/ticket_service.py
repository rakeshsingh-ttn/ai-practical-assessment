import csv
import io
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from src.backend.app.exceptions import (
    CommentNotAllowedError,
    NotFoundError,
    TicketNotEditableError,
)
from src.backend.app.models.entities import Comment, Ticket, TicketPriority, TicketStatus, User
from src.backend.app.schemas import CommentCreate, TicketCreate, TicketUpdate
from src.backend.app.services.ticket_status import (
    COMMENT_ALLOWED_STATUSES,
    EDITABLE_STATUSES,
    transition,
)


def get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user:
        raise NotFoundError("User", user_id)
    return user


def get_ticket_or_404(db: Session, ticket_id: int) -> Ticket:
    ticket = db.execute(
        select(Ticket)
        .options(joinedload(Ticket.creator), joinedload(Ticket.assignee))
        .where(Ticket.id == ticket_id)
    ).scalar_one_or_none()
    if not ticket:
        raise NotFoundError("Ticket", ticket_id)
    return ticket


def list_tickets(
    db: Session,
    *,
    status: TicketStatus | None = None,
    priority: TicketPriority | None = None,
    q: str | None = None,
    assigned_to: int | None = None,
    created_by: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Ticket], int]:
    query = select(Ticket).options(joinedload(Ticket.creator), joinedload(Ticket.assignee))

    if status:
        query = query.where(Ticket.status == status)
    if priority:
        query = query.where(Ticket.priority == priority)
    if assigned_to is not None:
        query = query.where(Ticket.assigned_to == assigned_to)
    if created_by is not None:
        query = query.where(Ticket.created_by == created_by)
    if q:
        pattern = f"%{q}%"
        query = query.where(
            or_(Ticket.title.ilike(pattern), Ticket.description.ilike(pattern))
        )

    count_query = select(func.count()).select_from(Ticket)
    if status:
        count_query = count_query.where(Ticket.status == status)
    if priority:
        count_query = count_query.where(Ticket.priority == priority)
    if assigned_to is not None:
        count_query = count_query.where(Ticket.assigned_to == assigned_to)
    if created_by is not None:
        count_query = count_query.where(Ticket.created_by == created_by)
    if q:
        pattern = f"%{q}%"
        count_query = count_query.where(
            or_(Ticket.title.ilike(pattern), Ticket.description.ilike(pattern))
        )
    total = db.execute(count_query).scalar_one()

    tickets = db.execute(
        query.order_by(Ticket.updated_at.desc()).limit(limit).offset(offset)
    ).unique().scalars().all()

    return list(tickets), total


def create_ticket(db: Session, data: TicketCreate) -> Ticket:
    get_user_or_404(db, data.created_by)
    if data.assigned_to is not None:
        get_user_or_404(db, data.assigned_to)

    ticket = Ticket(
        title=data.title,
        description=data.description,
        priority=data.priority,
        status=TicketStatus.OPEN,
        assigned_to=data.assigned_to,
        created_by=data.created_by,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return get_ticket_or_404(db, ticket.id)


def update_ticket(db: Session, ticket_id: int, data: TicketUpdate) -> Ticket:
    ticket = get_ticket_or_404(db, ticket_id)

    if ticket.status not in EDITABLE_STATUSES:
        raise TicketNotEditableError(ticket.status.value)

    if data.title is not None:
        ticket.title = data.title
    if data.description is not None:
        ticket.description = data.description
    if data.priority is not None:
        ticket.priority = data.priority
    if data.assigned_to is not None:
        get_user_or_404(db, data.assigned_to)
        ticket.assigned_to = data.assigned_to

    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    return get_ticket_or_404(db, ticket.id)


def change_ticket_status(db: Session, ticket_id: int, target: TicketStatus) -> Ticket:
    ticket = get_ticket_or_404(db, ticket_id)
    transition(ticket, target)
    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    return get_ticket_or_404(db, ticket.id)


def list_comments(db: Session, ticket_id: int) -> list[Comment]:
    get_ticket_or_404(db, ticket_id)
    return list(
        db.execute(
            select(Comment)
            .options(joinedload(Comment.author))
            .where(Comment.ticket_id == ticket_id)
            .order_by(Comment.created_at.asc())
        ).unique().scalars().all()
    )


def create_comment(db: Session, ticket_id: int, data: CommentCreate) -> Comment:
    ticket = get_ticket_or_404(db, ticket_id)
    if ticket.status not in COMMENT_ALLOWED_STATUSES:
        raise CommentNotAllowedError(ticket.status.value)

    get_user_or_404(db, data.created_by)
    comment = Comment(
        ticket_id=ticket_id,
        message=data.message,
        created_by=data.created_by,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    result = db.execute(
        select(Comment).options(joinedload(Comment.author)).where(Comment.id == comment.id)
    ).unique().scalar_one()
    return result


def export_tickets_csv(db: Session, created_by: int) -> str:
    get_user_or_404(db, created_by)
    tickets, _ = list_tickets(db, created_by=created_by, limit=10000, offset=0)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "title", "description", "priority", "status",
        "assigned_to", "assignee_name", "created_by", "creator_name",
        "created_at", "updated_at",
    ])
    for t in tickets:
        writer.writerow([
            t.id,
            t.title,
            t.description,
            t.priority.value,
            t.status.value,
            t.assigned_to or "",
            t.assignee.name if t.assignee else "",
            t.created_by,
            t.creator.name if t.creator else "",
            t.created_at.isoformat(),
            t.updated_at.isoformat(),
        ])
    return output.getvalue()
