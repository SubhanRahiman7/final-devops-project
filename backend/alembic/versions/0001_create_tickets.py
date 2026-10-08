"""create tickets table

Revision ID: 0001
Revises:
"""
import sqlalchemy as sa

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    now = sa.func.now()
    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("subject", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("category", sa.String(20), nullable=False, server_default="technical"),
        sa.Column("requester", sa.String(120), nullable=False, server_default=""),
        sa.Column("assignee", sa.String(100), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=now),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=now),
    )
    op.create_index("ix_tickets_status", "tickets", ["status"])


def downgrade() -> None:
    op.drop_index("ix_tickets_status", table_name="tickets")
    op.drop_table("tickets")
