"""add_tipo_usuario

Revision ID: c58d6b403529
Revises: fdd76123a2d1
Create Date: 2026-10-14 22:28:27.348590
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c58d6b403529"
down_revision: Union[str, Sequence[str], None] = "fdd76123a2d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usuario_empresa",
        sa.Column(
            "tipo",
            sa.String(length=20),
            nullable=False,
            server_default="comum",
        ),
    )


def downgrade() -> None:
    op.drop_column("usuario_empresa", "tipo")