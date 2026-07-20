"""add check constraints for enum columns

Revision ID: 002
Revises: 001
Create Date: 2026-07-20
"""

from typing import Sequence, Union

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_tickets_status",
        "tickets",
        "status IN ('Open', 'In Progress', 'Resolved', 'Closed', 'Cancelled')",
    )
    op.create_check_constraint(
        "ck_tickets_priority",
        "tickets",
        "priority IN ('Low', 'Medium', 'High')",
    )
    op.create_check_constraint(
        "ck_users_role",
        "users",
        "role IN ('Admin', 'Agent', 'Manager', 'Requester')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_role", "users", type_="check")
    op.drop_constraint("ck_tickets_priority", "tickets", type_="check")
    op.drop_constraint("ck_tickets_status", "tickets", type_="check")
