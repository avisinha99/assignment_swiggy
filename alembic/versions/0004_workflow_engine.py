"""workflow engine

Revision ID: 0004_workflow_engine
Revises: 0003_issues_core
Create Date: 2026-04-25

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0004_workflow_engine"
down_revision = "0003_issues_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workflow_statuses",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("project_id", "name", name="uq_workflow_statuses_project_name"),
    )
    op.create_index("ix_workflow_statuses_project_id", "workflow_statuses", ["project_id"])

    op.create_table(
        "workflow_transitions",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("from_status", sa.String(length=50), nullable=False),
        sa.Column("to_status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("project_id", "from_status", "to_status", name="uq_workflow_transitions_unique"),
    )
    op.create_index("ix_workflow_transitions_project_id", "workflow_transitions", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_workflow_transitions_project_id", table_name="workflow_transitions")
    op.drop_table("workflow_transitions")

    op.drop_index("ix_workflow_statuses_project_id", table_name="workflow_statuses")
    op.drop_table("workflow_statuses")
