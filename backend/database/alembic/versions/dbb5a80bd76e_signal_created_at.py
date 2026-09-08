"""signal created at

``signal.created_at`` — when the analysis actually finished, to the second.
``signal_date`` is a calendar date with no time of day, which was never
enough to place a signal on an intraday chart. NULL on existing rows;
backend/scripts/backfill_signal_timestamps.py recovers a best-effort value
from each row's trace file where one exists.

Revision ID: dbb5a80bd76e
Revises: 8fbaa3bb5d4b
Create Date: 2026-09-08 22:20:24.837020

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "dbb5a80bd76e"
down_revision: Union[str, Sequence[str], None] = "8fbaa3bb5d4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("signal")}
    if "created_at" not in existing:
        op.add_column("signal", sa.Column("created_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("signal", "created_at")
