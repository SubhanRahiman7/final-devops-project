from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models import Ticket

# (subject, description, status, priority, category, requester, assignee)
DEMO_TICKETS = [
    ("Cannot log in after password reset", "Reset e-mail arrives but the link is expired", "open", "urgent", "account", "meera@example.com", "Subhan"),
    ("Invoice shows the wrong amount", "Charged twice for the March plan", "in_progress", "high", "billing", "arjun@example.com", "Asha"),
    ("Dashboard is slow in the morning", "Charts take about 20 s to load", "in_progress", "medium", "technical", "riya@example.com", "Ravi"),
    ("Export to CSV is missing a column", "The 'assignee' column is not exported", "open", "low", "technical", "kabir@example.com", ""),
    ("Change the e-mail on my account", "Need to move the account to a new address", "resolved", "low", "account", "isha@example.com", "Asha"),
    ("Refund for cancelled order", "Order was cancelled within 24 hours", "resolved", "medium", "billing", "dev@example.com", "Subhan"),
    ("API returns 500 on large uploads", "Files above 10 MB fail", "open", "high", "technical", "nina@example.com", "Ravi"),
]


def seed_demo_data(db: Session) -> int:
    """Insert sample tickets, only when the table is empty.

    Several replicas start at the same time; a PostgreSQL advisory lock (held until commit)
    makes sure that only one of them seeds, instead of every replica inserting its own copy.
    """
    if db.get_bind().dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(2101)"))
    if db.scalar(select(func.count()).select_from(Ticket)):
        db.rollback()  # releases the lock
        return 0
    for subject, description, status, priority, category, requester, assignee in DEMO_TICKETS:
        db.add(
            Ticket(
                subject=subject,
                description=description,
                status=status,
                priority=priority,
                category=category,
                requester=requester,
                assignee=assignee,
            )
        )
    db.commit()
    return len(DEMO_TICKETS)
