"""create slides table

Revision ID: 523c149a530e
Revises: d67adf15a46d
Create Date: 2025-12-27 16:12:28.040171+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '523c149a530e'
down_revision: Union[str, None] = 'd67adf15a46d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "slides",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("subtitle", sa.String(length=200), nullable=True),
        sa.Column("link_url", sa.String(length=500), nullable=True),
        sa.Column("alt_text", sa.String(length=200), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("thumb_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_slides_active_order", "slides", ["is_active", "sort_order"])
    op.create_index("ix_slides_sort_order", "slides", ["sort_order"])
    op.create_index("ix_slides_is_active", "slides", ["is_active"])
    op.create_index("ix_slides_starts_at", "slides", ["starts_at"])
    op.create_index("ix_slides_ends_at", "slides", ["ends_at"])

def downgrade():
    op.drop_index("ix_slides_active_order", table_name="slides")
    op.drop_index("ix_slides_sort_order", table_name="slides")
    op.drop_index("ix_slides_is_active", table_name="slides")
    op.drop_index("ix_slides_starts_at", table_name="slides")
    op.drop_index("ix_slides_ends_at", table_name="slides")
    op.drop_table("slides")
