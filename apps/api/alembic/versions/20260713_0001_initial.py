"""Initial operational, context, evidence and workflow schema.

Revision ID: 20260713_0001
Revises:
"""

from collections.abc import Sequence

from agi_server.db import Base
from alembic import op

revision: str = "20260713_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
