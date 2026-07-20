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
    # SQLite cannot ALTER constraints; batch mode recreates the table.
    with op.batch_alter_table("tickets") as batch_op:
        batch_op.create_check_constraint(
            "ck_tickets_status",
            "status IN ('Open', 'In Progress', 'Resolved', 'Closed', 'Cancelled')",
        )
        batch_op.create_check_constraint(
            "ck_tickets_priority",
            "priority IN ('Low', 'Medium', 'High')",
        )

    with op.batch_alter_table("users") as batch_op:
        batch_op.create_check_constraint(
            "ck_users_role",
            "role IN ('Admin', 'Agent', 'Manager', 'Requester')",
        )


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("ck_users_role", type_="check")

    with op.batch_alter_table("tickets") as batch_op:
        batch_op.drop_constraint("ck_tickets_priority", type_="check")
        batch_op.drop_constraint("ck_tickets_status", type_="check")
