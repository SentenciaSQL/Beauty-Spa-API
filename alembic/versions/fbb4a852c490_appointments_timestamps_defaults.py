"""appointments timestamps defaults

Revision ID: fbb4a852c490
Revises: 441b65776cdd
Create Date: 2025-12-27 03:49:28.704599+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fbb4a852c490'
down_revision: Union[str, None] = '441b65776cdd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # si alguna fila vieja tiene NULL (por si acaso)
    op.execute("UPDATE appointments SET created_at = NOW() WHERE created_at IS NULL")
    op.execute("UPDATE appointments SET updated_at = NOW() WHERE updated_at IS NULL")

    op.alter_column(
        "appointments",
        "created_at",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        server_default=sa.text("NOW()"),
        nullable=False,
    )
    op.alter_column(
        "appointments",
        "updated_at",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        server_default=sa.text("NOW()"),
        nullable=False,
    )

def downgrade():
    op.alter_column("appointments", "updated_at", server_default=None)
    op.alter_column("appointments", "created_at", server_default=None)
