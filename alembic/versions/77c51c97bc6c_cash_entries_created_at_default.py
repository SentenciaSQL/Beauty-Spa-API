"""cash_entries created_at default

Revision ID: 77c51c97bc6c
Revises: 55f4be2d3db7
Create Date: 2025-12-27 02:10:47.251029+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '77c51c97bc6c'
down_revision: Union[str, None] = '55f4be2d3db7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1) Si hay filas viejas con NULL, arreglarlas (por seguridad)
    op.execute("UPDATE cash_entries SET created_at = NOW() WHERE created_at IS NULL")

    # 2) Poner default a nivel DB
    op.alter_column(
        "cash_entries",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.text("NOW()"),
        nullable=False,
    )

def downgrade():
    op.alter_column(
        "cash_entries",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        nullable=False,
    )