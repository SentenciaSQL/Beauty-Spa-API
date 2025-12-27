"""manual add image_url columns

Revision ID: d67adf15a46d
Revises: fed0958fcc30
Create Date: 2025-12-27 05:22:28.409143+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd67adf15a46d'
down_revision: Union[str, None] = 'fed0958fcc30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column("services", sa.Column("image_url", sa.String(length=500), nullable=True))
    op.add_column("products", sa.Column("image_url", sa.String(length=500), nullable=True))
    op.add_column("users", sa.Column("image_url", sa.String(length=500), nullable=True))

def downgrade():
    op.drop_column("users", "image_url")
    op.drop_column("products", "image_url")
    op.drop_column("services", "image_url")
