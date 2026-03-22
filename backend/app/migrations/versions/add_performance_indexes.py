"""Performance indexes migration for common query patterns.

Revision ID: add_performance_indexes
Create Date: 2026-03-22
Revises:
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision: str = "add_performance_indexes"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes for common query patterns.

    @MX:NOTE: Performance optimization indexes
    These indexes optimize the most common query patterns:
    - User lookups by family and email
    - Child profile lookups by family and user
    - Task filtering by status and date
    - Point transaction lookups by child and date
    """

    # User indexes
    # Index for finding users by family (common in multi-parent households)
    op.create_index(
        "ix_users_family_id",
        "users",
        ["family_id"],
        unique=False,
    )

    # Index for email lookups (already unique, but explicit index helps)
    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=True,
    )

    # Child profile indexes
    # Index for finding children by parent (very common query)
    op.create_index(
        "ix_child_profiles_parent_id",
        "child_profiles",
        ["parent_id"],
        unique=False,
    )

    # Index for family-wide child listings
    op.create_index(
        "ix_child_profiles_family_id",
        "child_profiles",
        ["family_id"],
        unique=False,
    )

    # Compound index for active children in a family
    op.create_index(
        "ix_child_profiles_family_id_is_active",
        "child_profiles",
        ["family_id", "is_active"],
        unique=False,
    )

    # Task indexes
    # Compound index for pending tasks by child (dashboard query)
    op.create_index(
        "ix_tasks_child_id_status",
        "tasks",
        ["child_id", "status"],
        unique=False,
    )

    # Index for task date filtering (calendar views)
    op.create_index(
        "ix_tasks_due_date",
        "tasks",
        ["due_date"],
        unique=False,
    )

    # Index for active tasks only
    op.create_index(
        "ix_tasks_is_active",
        "tasks",
        ["is_active"],
        unique=False,
    )

    # Compound index for active pending tasks (common dashboard query)
    op.create_index(
        "ix_tasks_child_id_status_is_active",
        "tasks",
        ["child_id", "status", "is_active"],
        unique=False,
    )

    # Task completion indexes
    # Compound index for streak calculations (child + date)
    op.create_index(
        "ix_task_completions_child_id_completed_date",
        "task_completions",
        ["child_id", "completed_date"],
        unique=False,
    )

    # Point transaction indexes
    # Compound index for transaction history (child + date)
    op.create_index(
        "ix_point_transactions_child_id_created_at",
        "point_transactions",
        ["child_id", "created_at"],
        unique=False,
    )

    # Compound index for transaction type filtering
    op.create_index(
        "ix_point_transactions_child_id_type",
        "point_transactions",
        ["child_id", "type"],
        unique=False,
    )

    # Point balance indexes
    # Already has child_id unique index, no additional indexes needed

    # Point freeze indexes
    # Index for active freezes by child
    op.create_index(
        "ix_point_freezes_child_id_status",
        "point_freezes",
        ["child_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    """Remove performance indexes."""

    # User indexes
    op.drop_index("ix_users_family_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")

    # Child profile indexes
    op.drop_index("ix_child_profiles_parent_id", table_name="child_profiles")
    op.drop_index("ix_child_profiles_family_id", table_name="child_profiles")
    op.drop_index("ix_child_profiles_family_id_is_active", table_name="child_profiles")

    # Task indexes
    op.drop_index("ix_tasks_child_id_status", table_name="tasks")
    op.drop_index("ix_tasks_due_date", table_name="tasks")
    op.drop_index("ix_tasks_is_active", table_name="tasks")
    op.drop_index("ix_tasks_child_id_status_is_active", table_name="tasks")

    # Task completion indexes
    op.drop_index(
        "ix_task_completions_child_id_completed_date", table_name="task_completions"
    )

    # Point transaction indexes
    op.drop_index(
        "ix_point_transactions_child_id_created_at", table_name="point_transactions"
    )
    op.drop_index("ix_point_transactions_child_id_type", table_name="point_transactions")

    # Point freeze indexes
    op.drop_index("ix_point_freezes_child_id_status", table_name="point_freezes")
