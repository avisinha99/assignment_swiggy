"""comments watchers notifications

Revision ID: 0006_comments_watchers_notifications
Revises: 0005_activity_log
Create Date: 2026-04-25

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0006_comments_notifs"
down_revision = "0005_activity_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "comments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("issue_id", sa.String(length=36), nullable=False),
        sa.Column("author_id", sa.String(length=36), nullable=False),
        sa.Column("parent_comment_id", sa.Integer(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["issue_id"], ["issues.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["parent_comment_id"], ["comments.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_comments_issue_id", "comments", ["issue_id", "id"])
    op.create_index("ix_comments_parent_comment_id", "comments", ["parent_comment_id"])

    op.create_table(
        "issue_watchers",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("issue_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["issue_id"], ["issues.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("issue_id", "user_id", name="uq_issue_watchers_issue_user"),
    )
    op.create_index("ix_issue_watchers_issue_id", "issue_watchers", ["issue_id"])
    op.create_index("ix_issue_watchers_user_id", "issue_watchers", ["user_id"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id", "id"])


def downgrade() -> None:
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")

    op.drop_index("ix_issue_watchers_user_id", table_name="issue_watchers")
    op.drop_index("ix_issue_watchers_issue_id", table_name="issue_watchers")
    op.drop_table("issue_watchers")

    op.drop_index("ix_comments_parent_comment_id", table_name="comments")
    op.drop_index("ix_comments_issue_id", table_name="comments")
    op.drop_table("comments")
