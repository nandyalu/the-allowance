"""agent run thinking

``agentrun.thinking`` — the model's own reasoning behind a decision, which was
generated, paid for, and thrown away.

Ollama returns it on ``/v1/chat/completions`` as a ``reasoning`` field beside
the content, and ``ChatOpenAI`` drops it deliberately: its docstring says it
targets the official OpenAI specification and does not extract "non-standard
response fields added by third-party providers". So the record kept a
606-character answer while discarding 4,034 characters of the reasoning that
produced it, and paid for both — the reasoning is most of what the model
generates. See JOURNEY.md's 2026-09-09 entry.

NULL on existing rows, on a pass that never asked, and on any provider whose
client does not return it. Nothing is backfilled: the text was never stored,
and re-running a pass now would answer a different day's question.

Revision ID: c8e5a71b0d93
Revises: b6d21e84f7c0
Create Date: 2026-09-09 20:14:37.518902

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c8e5a71b0d93"
down_revision: Union[str, Sequence[str], None] = "b6d21e84f7c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("agentrun")}
    if "thinking" not in existing:
        op.add_column("agentrun", sa.Column("thinking", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("agentrun", "thinking")
