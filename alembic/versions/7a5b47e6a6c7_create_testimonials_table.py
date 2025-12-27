"""create testimonials table

Revision ID: 7a5b47e6a6c7
Revises: 5076f9b34f20
Create Date: 2025-12-27 18:10:27.476619+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a5b47e6a6c7'
down_revision: Union[str, None] = '5076f9b34f20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "testimonials",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("testimonial_date", sa.Date(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("thumb_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_testimonials_order", "testimonials", ["sort_order", "id"])
    op.create_index("ix_testimonials_sort_order", "testimonials", ["sort_order"])

def downgrade():
    op.drop_index("ix_testimonials_order", table_name="testimonials")
    op.drop_index("ix_testimonials_sort_order", table_name="testimonials")
    op.drop_table("testimonials")
