"""ticker webull category

``tickerstatus.webull_category`` — "US_STOCK" or "US_ETF", whichever this
ticker's market-data calls actually answer on. It was kept in a process-local
dict in backend/services/quotes.py, so every restart threw it away and each
ticker paid an extra probe request to learn it again. See docs/changelog.md,
2026-09-09: that surplus request was part of what had Webull refusing
524 of one day's calls, across 22 restarts.

NULL on existing rows and until a ticker first answers, which reads the same
as "not learned yet" and simply costs the probe once more.

Revision ID: a3f7c02e9b41
Revises: dbb5a80bd76e
Create Date: 2026-09-09 17:05:11.204871

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a3f7c02e9b41"
down_revision: Union[str, Sequence[str], None] = "dbb5a80bd76e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("tickerstatus")}
    if "webull_category" not in existing:
        op.add_column("tickerstatus", sa.Column("webull_category", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("tickerstatus", "webull_category")
