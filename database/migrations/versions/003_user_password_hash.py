"""add password_hash to users

Revision ID: 003
Revises: 002
Create Date: 2026-07-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from src.backend.app.auth.passwords import DEFAULT_SEED_PASSWORD, hash_password

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("password_hash", sa.String(length=255), nullable=True))

    connection = op.get_bind()
    hashed = hash_password(DEFAULT_SEED_PASSWORD)
    connection.execute(
        sa.text("UPDATE users SET password_hash = :password_hash WHERE password_hash IS NULL"),
        {"password_hash": hashed},
    )

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("password_hash", existing_type=sa.String(length=255), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("password_hash")
