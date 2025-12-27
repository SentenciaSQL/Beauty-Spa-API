"""add payment method and nullable concept to cash_entries

Revision ID: 55f4be2d3db7
Revises: ca37766eebac
Create Date: 2025-12-27 01:37:08.292196+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

payment_method_enum = sa.Enum(
    'CASH',
    'CARD',
    'TRANSFER',
    name='paymentmethod'
)

# revision identifiers, used by Alembic.
revision: str = '55f4be2d3db7'
down_revision: Union[str, None] = 'ca37766eebac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1Crear ENUM en PostgreSQL (si no existe)
    payment_method_enum.create(op.get_bind(), checkfirst=True)

    # Agregar columna method
    op.add_column(
        'cash_entries',
        sa.Column(
            'method',
            payment_method_enum,
            nullable=False,
            server_default='CASH',  # para filas existentes
        )
    )

    # Quitar default de servidor (opcional pero recomendado)
    op.alter_column('cash_entries', 'method', server_default=None)

    # Cambiar concept a nullable=True
    op.alter_column(
        'cash_entries',
        'concept',
        existing_type=sa.Text(),
        nullable=True,
    )


def downgrade():
    # revertir nullable
    op.alter_column(
        'cash_entries',
        'concept',
        existing_type=sa.Text(),
        nullable=False,
    )

    # eliminar columna
    op.drop_column('cash_entries', 'method')

    # eliminar enum (solo si nadie más lo usa)
    payment_method_enum.drop(op.get_bind(), checkfirst=True)
