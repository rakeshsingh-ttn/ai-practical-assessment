from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from src.backend.app.database import get_db
from src.backend.app.models.entities import TicketPriority, TicketStatus
from src.backend.app.schemas import (
    CommentCreate,
    CommentOut,
    TicketCreate,
    TicketListOut,
    TicketOut,
    TicketStatusUpdate,
    TicketUpdate,
)
from src.backend.app.services import ticket_service

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("", response_model=TicketListOut)
def list_tickets(
    status: TicketStatus | None = None,
    priority: TicketPriority | None = None,
    q: str | None = None,
    assigned_to: int | None = None,
    created_by: int | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    tickets, total = ticket_service.list_tickets(
        db,
        status=status,
        priority=priority,
        q=q,
        assigned_to=assigned_to,
        created_by=created_by,
        limit=limit,
        offset=offset,
    )
    return TicketListOut(items=tickets, total=total, limit=limit, offset=offset)


@router.post("", response_model=TicketOut, status_code=201)
def create_ticket(data: TicketCreate, db: Session = Depends(get_db)):
    return ticket_service.create_ticket(db, data)


@router.get("/export")
def export_tickets(created_by: int, db: Session = Depends(get_db)):
    csv_content = ticket_service.export_tickets_csv(db, created_by)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="tickets_user_{created_by}.csv"'
        },
    )


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    return ticket_service.get_ticket_or_404(db, ticket_id)


@router.patch("/{ticket_id}", response_model=TicketOut)
def update_ticket(ticket_id: int, data: TicketUpdate, db: Session = Depends(get_db)):
    return ticket_service.update_ticket(db, ticket_id, data)


@router.post("/{ticket_id}/status", response_model=TicketOut)
def change_status(ticket_id: int, data: TicketStatusUpdate, db: Session = Depends(get_db)):
    return ticket_service.change_ticket_status(db, ticket_id, data.status)


@router.get("/{ticket_id}/comments", response_model=list[CommentOut])
def list_comments(ticket_id: int, db: Session = Depends(get_db)):
    return ticket_service.list_comments(db, ticket_id)


@router.post("/{ticket_id}/comments", response_model=CommentOut, status_code=201)
def create_comment(ticket_id: int, data: CommentCreate, db: Session = Depends(get_db)):
    return ticket_service.create_comment(db, ticket_id, data)
