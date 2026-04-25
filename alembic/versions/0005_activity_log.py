"""activity log

Revision ID: 0005_activity_log
Revises: 0004_workflow_engine
Create Date: 2026-04-25

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0005_activity_log"
down_revision = "0004_workflow_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "activity",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("issue_id", sa.String(length=36), nullable=True),
        sa.Column("actor_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["issue_id"], ["issues.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_activity_project_id", "activity", ["project_id", "id"])
    op.create_index("ix_activity_issue_id", "activity", ["issue_id", "id"])


def downgrade() -> None:
    op.drop_index("ix_activity_issue_id", table_name="activity")
    op.drop_index("ix_activity_project_id", table_name="activity")
    op.drop_table("activity")
