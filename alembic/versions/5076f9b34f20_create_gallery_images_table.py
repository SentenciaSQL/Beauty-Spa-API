"""create gallery_images table

Revision ID: 5076f9b34f20
Revises: 523c149a530e
Create Date: 2025-12-27 17:34:07.254494+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5076f9b34f20'
down_revision: Union[str, None] = '523c149a530e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "gallery_images",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=120), nullable=True),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("alt_text", sa.String(length=200), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("thumb_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_gallery_order", "gallery_images", ["sort_order", "id"])
    op.create_index("ix_gallery_images_sort_order", "gallery_images", ["sort_order"])

def downgrade():
    op.drop_index("ix_gallery_order", table_name="gallery_images")
    op.drop_index("ix_gallery_images_sort_order", table_name="gallery_images")
    op.drop_table("gallery_images")