"""issues core

Revision ID: 0003_issues_core
Revises: 0002_projects_and_membership
Create Date: 2026-04-25

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0003_issues_core"
down_revision = "0002_projects_and_membership"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sprints",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("state", sa.String(length=20), nullable=False, server_default=sa.text("'planned'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_sprints_project_id", "sprints", ["project_id"])
    op.create_index("ix_sprints_state", "sprints", ["state"])

    op.create_table(
        "issues",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("issue_key", sa.String(length=40), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default=sa.text("'to_do'")),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default=sa.text("'medium'")),
        sa.Column("assignee_id", sa.String(length=36), nullable=True),
        sa.Column("reporter_id", sa.String(length=36), nullable=False),
        sa.Column("sprint_id", sa.String(length=36), nullable=True),
        sa.Column("story_points", sa.Integer(), nullable=True),
        sa.Column("parent_id", sa.String(length=36), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["assignee_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["parent_id"], ["issues.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["sprint_id"], ["sprints.id"]),
    )
    op.create_index("ix_issues_issue_key", "issues", ["issue_key"], unique=True)
    op.create_index("ix_issues_project_id", "issues", ["project_id"])
    op.create_index("ix_issues_status", "issues", ["status"])
    op.create_index("ix_issues_assignee_id", "issues", ["assignee_id"])
    op.create_index("ix_issues_parent_id", "issues", ["parent_id"])

    op.create_table(
        "issue_labels",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("issue_id", sa.String(length=36), nullable=False),
        sa.Column("label", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(["issue_id"], ["issues.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("issue_id", "label", name="uq_issue_labels_issue_label"),
    )
    op.create_index("ix_issue_labels_issue_id", "issue_labels", ["issue_id"])
    op.create_index("ix_issue_labels_label", "issue_labels", ["label"])


def downgrade() -> None:
    op.drop_index("ix_issue_labels_label", table_name="issue_labels")
    op.drop_index("ix_issue_labels_issue_id", table_name="issue_labels")
    op.drop_table("issue_labels")

    op.drop_index("ix_issues_parent_id", table_name="issues")
    op.drop_index("ix_issues_assignee_id", table_name="issues")
    op.drop_index("ix_issues_status", table_name="issues")
    op.drop_index("ix_issues_project_id", table_name="issues")
    op.drop_index("ix_issues_issue_key", table_name="issues")
    op.drop_table("issues")

    op.drop_index("ix_sprints_state", table_name="sprints")
    op.drop_index("ix_sprints_project_id", table_name="sprints")
    op.drop_table("sprints")
