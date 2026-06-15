"""coaching_state: 세션별 코칭 진척도 스냅샷

Revision ID: 0002_coaching_state
Revises: 0001_initial
Create Date: 2026-06-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_coaching_state"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "coaching_state",
        sa.Column("thread_id", sa.String(length=64), nullable=False),
        sa.Column("state", sa.JSON(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("thread_id"),
    )


def downgrade() -> None:
    op.drop_table("coaching_state")
