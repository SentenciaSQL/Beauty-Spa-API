"""add image_url to service product user

Revision ID: fed0958fcc30
Revises: fbb4a852c490
Create Date: 2025-12-27 05:11:49.460483+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fed0958fcc30'
down_revision: Union[str, None] = 'fbb4a852c490'
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
