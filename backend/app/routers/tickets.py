from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Ticket
from app.schemas import TicketCreate, TicketOut, TicketStats, TicketUpdate

router = APIRouter(prefix="/api/tickets", tags=["tickets"])

STATUSES = ("open", "in_progress", "resolved")
PRIORITIES = ("low", "medium", "high", "urgent")
CATEGORIES = ("billing", "technical", "account", "other")


def _counts(db: Session, column) -> dict[str, int]:
    return dict(db.execute(select(column, func.count()).group_by(column)).all())


def _get_or_404(db: Session, ticket_id: int) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ticket not found")
    return ticket


@router.get("", response_model=list[TicketOut])
def list_tickets(
    status_filter: str | None = Query(default=None, alias="status"),
    priority: str | None = None,
    db: Session = Depends(get_db),
):
    query = select(Ticket).order_by(Ticket.updated_at.desc(), Ticket.id.desc())
    if status_filter:
        query = query.where(Ticket.status == status_filter)
    if priority:
        query = query.where(Ticket.priority == priority)
    return db.scalars(query).all()


# declared before "/{ticket_id}" so that "stats" is not parsed as an id
@router.get("/stats", response_model=TicketStats)
def ticket_stats(db: Session = Depends(get_db)):
    by_status = _counts(db, Ticket.status)
    by_priority = _counts(db, Ticket.priority)
    by_category = _counts(db, Ticket.category)
    total = sum(by_status.values())
    resolved = by_status.get("resolved", 0)
    open_urgent = db.scalar(
        select(func.count()).select_from(Ticket).where(
            Ticket.priority == "urgent", Ticket.status != "resolved"
        )
    )
    return TicketStats(
        total=total,
        by_status={s: by_status.get(s, 0) for s in STATUSES},
        by_priority={p: by_priority.get(p, 0) for p in PRIORITIES},
        by_category={c: by_category.get(c, 0) for c in CATEGORIES},
        resolution_rate=round(resolved / total * 100, 1) if total else 0.0,
        open_urgent=open_urgent or 0,
    )


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, ticket_id)


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    ticket = Ticket(**payload.model_dump())
    db.add(ticket)
    db.commit()
    return ticket


@router.put("/{ticket_id}", response_model=TicketOut)
def update_ticket(ticket_id: int, payload: TicketUpdate, db: Session = Depends(get_db)):
    ticket = _get_or_404(db, ticket_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(ticket, field, value)
    db.commit()
    return ticket


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    db.delete(_get_or_404(db, ticket_id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
