"""agent run turns

``agentrun.turns`` — every turn of a decision pass, not only the last.

A pass has had more than one turn since the refusal retry was built: the retry
rebuilds the prompt and calls the model again. But ``prompt`` and ``response``
hold one value each, and the retry overwrote them — so a two-turn pass was
published as though it were one, against a site whose central claim is that
every prompt the agent saw is on the record, word for word.

That was a small gap while a retry was the only second turn, and it stopped
being small on 2026-09-10, when the agent gained a way to ask to read an
analysis mid-pass. See JOURNEY.md's entry for that date.

JSON, oldest first: a list of {"prompt", "response", "thinking"}. ``prompt``
and ``response`` stay the LAST turn, which is the one the accepted orders were
screened from and what every existing reader expects.

NULL on every existing row, and nothing is backfilled. Those passes did hold
one turn, and it is already in ``prompt``/``response`` — inventing a list to
match a new shape would be writing a record nobody kept.

Revision ID: d1f4a63c85b2
Revises: c8e5a71b0d93
Create Date: 2026-09-10 13:05:11.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d1f4a63c85b2"
down_revision: Union[str, Sequence[str], None] = "c8e5a71b0d93"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("agentrun")}
    if "turns" not in existing:
        op.add_column("agentrun", sa.Column("turns", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("agentrun", "turns")
