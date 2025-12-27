"""add audit_logs table

Revision ID: beed82a9f98b
Revises: 7a5b47e6a6c7
Create Date: 2025-12-27 18:46:51.851225+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'beed82a9f98b'
down_revision: Union[str, None] = '7a5b47e6a6c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("table_name", sa.String(length=80), nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=10), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("before", sa.JSON(), nullable=True),
        sa.Column("after", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_index("ix_audit_logs_table_name", "audit_logs", ["table_name"])
    op.create_index("ix_audit_logs_record_id", "audit_logs", ["record_id"])
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
    op.create_index("ix_audit_table_record", "audit_logs", ["table_name", "record_id"])


def downgrade():
    op.drop_index("ix_audit_table_record", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_user_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_record_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_table_name", table_name="audit_logs")
    op.drop_table("audit_logs")
