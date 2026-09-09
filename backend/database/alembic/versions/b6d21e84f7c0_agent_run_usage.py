"""agent run usage

``agentrun.prompt_tokens`` / ``completion_tokens`` / ``seconds`` — what the
model calls in one decision pass cost, summed across the retry when there was
one. ``Signal`` has carried the same kind of telemetry for an analysis since
the cost work landed, but a decision pass stored its prompt and its answer in
full and not one token of what they cost. The agent wakes several times a day
and every prompt change moves the number, so it is a recurring cost the record
could not see.

NULL on existing rows and on any pass whose endpoint reports no usage — a zero
would read as a free call, which is the rule Signal's own columns already
follow. Nothing is backfilled: the counts come from the provider's usage block
and there is no honest way to recover one after the fact.

Revision ID: b6d21e84f7c0
Revises: a3f7c02e9b41
Create Date: 2026-09-09 19:41:52.663104

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b6d21e84f7c0"
down_revision: Union[str, Sequence[str], None] = "a3f7c02e9b41"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_COLUMNS = (
    ("prompt_tokens", sa.Integer()),
    ("completion_tokens", sa.Integer()),
    ("seconds", sa.Float()),
)


def upgrade() -> None:
    existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("agentrun")}
    for name, kind in _COLUMNS:
        if name not in existing:
            op.add_column("agentrun", sa.Column(name, kind, nullable=True))


def downgrade() -> None:
    for name, _ in _COLUMNS:
        op.drop_column("agentrun", name)
