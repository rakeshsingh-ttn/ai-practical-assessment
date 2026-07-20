"""Seed script: python -m src.backend.seed

All seeded users share the documented default password (see DEFAULT_SEED_PASSWORD).
"""

from sqlalchemy import select

from src.backend.app.auth.passwords import DEFAULT_SEED_PASSWORD, hash_password
from src.backend.app.database import SessionLocal
from src.backend.app.models.entities import (
    Comment,
    Ticket,
    TicketPriority,
    TicketStatus,
    User,
    UserRole,
)

# Runtime status changes must go through the state machine service.
# Seed data sets statuses directly for demo coverage across all states.

USERS = [
    {
        "name": "Alice Admin",
        "email": "alice@example.com",
        "role": UserRole.ADMIN,
        "password_hash": hash_password(DEFAULT_SEED_PASSWORD),
    },
    {
        "name": "Bob Agent",
        "email": "bob@example.com",
        "role": UserRole.AGENT,
        "password_hash": hash_password(DEFAULT_SEED_PASSWORD),
    },
    {
        "name": "Carol Manager",
        "email": "carol@example.com",
        "role": UserRole.MANAGER,
        "password_hash": hash_password(DEFAULT_SEED_PASSWORD),
    },
    {
        "name": "Dave Requester",
        "email": "dave@example.com",
        "role": UserRole.REQUESTER,
        "password_hash": hash_password(DEFAULT_SEED_PASSWORD),
    },
]

TICKETS = [
    {
        "title": "VPN not connecting",
        "description": "Cannot connect to corporate VPN from home office.",
        "priority": TicketPriority.HIGH,
        "status": TicketStatus.OPEN,
        "created_by": 4,
        "assigned_to": 2,
    },
    {
        "title": "Password reset needed",
        "description": "User locked out after too many failed attempts.",
        "priority": TicketPriority.MEDIUM,
        "status": TicketStatus.IN_PROGRESS,
        "created_by": 4,
        "assigned_to": 2,
    },
    {
        "title": "Email sync delay",
        "description": "Outlook not syncing new messages for 2 hours.",
        "priority": TicketPriority.MEDIUM,
        "status": TicketStatus.RESOLVED,
        "created_by": 4,
        "assigned_to": 2,
    },
    {
        "title": "Laptop battery replacement",
        "description": "Battery holds charge for less than 30 minutes.",
        "priority": TicketPriority.LOW,
        "status": TicketStatus.CLOSED,
        "created_by": 4,
        "assigned_to": 2,
    },
    {
        "title": "Software license request",
        "description": "Need Adobe Creative Cloud license for design team.",
        "priority": TicketPriority.LOW,
        "status": TicketStatus.CANCELLED,
        "created_by": 4,
        "assigned_to": None,
    },
    {
        "title": "Printer offline in Building A",
        "description": "Floor 3 printer shows offline status.",
        "priority": TicketPriority.HIGH,
        "status": TicketStatus.OPEN,
        "created_by": 1,
        "assigned_to": 2,
    },
    {
        "title": "New hire laptop setup",
        "description": "Provision laptop for new employee starting Monday.",
        "priority": TicketPriority.MEDIUM,
        "status": TicketStatus.IN_PROGRESS,
        "created_by": 3,
        "assigned_to": 2,
    },
    {
        "title": "Slack integration broken",
        "description": "Notifications from Jira not appearing in Slack.",
        "priority": TicketPriority.HIGH,
        "status": TicketStatus.RESOLVED,
        "created_by": 3,
        "assigned_to": 2,
    },
    {
        "title": "Monitor flickering",
        "description": "External monitor flickers intermittently.",
        "priority": TicketPriority.LOW,
        "status": TicketStatus.OPEN,
        "created_by": 4,
        "assigned_to": None,
    },
    {
        "title": "Access to shared drive",
        "description": "Need read access to Finance shared drive.",
        "priority": TicketPriority.MEDIUM,
        "status": TicketStatus.CLOSED,
        "created_by": 4,
        "assigned_to": 1,
    },
    {
        "title": "Conference room AV issue",
        "description": "Projector not displaying HDMI input.",
        "priority": TicketPriority.HIGH,
        "status": TicketStatus.IN_PROGRESS,
        "created_by": 1,
        "assigned_to": 2,
    },
    {
        "title": "Duplicate ticket test",
        "description": "This ticket was created by mistake.",
        "priority": TicketPriority.LOW,
        "status": TicketStatus.CANCELLED,
        "created_by": 3,
        "assigned_to": None,
    },
]

COMMENTS = [
    {"ticket_id": 1, "message": "Can you try restarting the VPN client?", "created_by": 2},
    {"ticket_id": 2, "message": "Reset link sent to your email.", "created_by": 2},
    {"ticket_id": 3, "message": "Restarted the mail sync service.", "created_by": 2},
    {"ticket_id": 3, "message": "Confirmed emails are syncing now.", "created_by": 4},
    {"ticket_id": 6, "message": "Checking network connectivity to printer.", "created_by": 2},
    {"ticket_id": 7, "message": "Laptop imaged and software installed.", "created_by": 2},
    {"ticket_id": 8, "message": "Webhook URL was misconfigured, fixed now.", "created_by": 2},
    {"ticket_id": 11, "message": "Ordered replacement HDMI cable.", "created_by": 2},
]


def seed() -> None:
    db = SessionLocal()
    try:
        existing_users = db.execute(select(User)).scalars().first()
        if existing_users:
            print("Database already seeded, skipping.")
            return

        for user_data in USERS:
            db.add(User(**user_data))
        db.flush()

        for ticket_data in TICKETS:
            db.add(Ticket(**ticket_data))
        db.flush()

        for comment_data in COMMENTS:
            db.add(Comment(**comment_data))

        db.commit()
        print("Seed data inserted successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
