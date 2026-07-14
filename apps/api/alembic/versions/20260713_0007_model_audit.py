"""Record content-safe model execution audit attributes.

Revision ID: 20260713_0007
Revises: 20260713_0006
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260713_0007"
down_revision: str | None = "20260713_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("workflow_step_runs", sa.Column("model_provider", sa.String(40)))
    op.add_column("workflow_step_runs", sa.Column("model_name", sa.String(160)))
    op.add_column("workflow_step_runs", sa.Column("data_classification", sa.String(30)))
    op.add_column("workflow_step_runs", sa.Column("redaction_applied", sa.Boolean()))


def downgrade() -> None:
    op.drop_column("workflow_step_runs", "redaction_applied")
    op.drop_column("workflow_step_runs", "data_classification")
    op.drop_column("workflow_step_runs", "model_name")
    op.drop_column("workflow_step_runs", "model_provider")
