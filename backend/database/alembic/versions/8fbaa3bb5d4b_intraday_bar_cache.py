"""intraday bar cache

``intradaybar`` — 1-minute OHLCV, one row per (ticker, timestamp). See
``IntradayBar`` in backend/database/models.py for why: a signal, an alert, or
a trade needs a real intraday price series to be placed on a chart at the
moment it actually happened, and the existing ``dailybar`` cache only ever
holds one row per calendar day.

Revision ID: 8fbaa3bb5d4b
Revises: f1a5c93e28b7
Create Date: 2026-09-08 22:19:58.844878

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "8fbaa3bb5d4b"
down_revision: Union[str, Sequence[str], None] = "f1a5c93e28b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if "intradaybar" not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table(
            "intradaybar",
            sa.Column("ticker", sa.String(), nullable=False),
            sa.Column("timestamp", sa.DateTime(), nullable=False),
            sa.Column("open", sa.Float(), nullable=False),
            sa.Column("high", sa.Float(), nullable=False),
            sa.Column("low", sa.Float(), nullable=False),
            sa.Column("close", sa.Float(), nullable=False),
            sa.Column("volume", sa.Float(), nullable=False),
            sa.PrimaryKeyConstraint("ticker", "timestamp"),
        )


def downgrade() -> None:
    op.drop_table("intradaybar")
