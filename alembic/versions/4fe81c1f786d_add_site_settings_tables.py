"""add site settings tables

Revision ID: 4fe81c1f786d
Revises: beed82a9f98b
Create Date: 2025-12-27 19:36:53.954991+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4fe81c1f786d'
down_revision: Union[str, None] = 'beed82a9f98b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # ---------- site_settings ----------
    op.create_table(
        "site_settings",
        sa.Column("id", sa.Integer(), primary_key=True),

        sa.Column("app_name", sa.String(length=120), nullable=False, server_default="Spa App"),
        sa.Column("tagline", sa.String(length=160), nullable=True),

        sa.Column("logo_main_url", sa.String(length=500), nullable=True),
        sa.Column("logo_sidebar_url", sa.String(length=500), nullable=True),
        sa.Column("logo_small_url", sa.String(length=500), nullable=True),

        sa.Column("whatsapp_phone_e164", sa.String(length=30), nullable=True),
        sa.Column("contact_phone", sa.String(length=30), nullable=True),
        sa.Column("contact_email", sa.String(length=150), nullable=True),

        sa.Column("address_text", sa.String(length=250), nullable=True),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("google_maps_iframe", sa.Text(), nullable=True),

        sa.Column("about_text", sa.Text(), nullable=True),
        sa.Column("terms_text", sa.Text(), nullable=True),
        sa.Column("privacy_text", sa.Text(), nullable=True),

        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),

        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # ---------- ENUM (create only if missing) ----------
    bind = op.get_bind()

    social_type_enum = postgresql.ENUM(
        "INSTAGRAM",
        "FACEBOOK",
        "X",
        "TIKTOK",
        "YOUTUBE",
        "WHATSAPP",
        "WEBSITE",
        name="socialtype",
        create_type=False,   # 👈 CLAVE: no autocreate
    )

    # crear enum si no existe
    social_type_enum.create(bind, checkfirst=True)

    # ---------- site_social_links ----------
    op.create_table(
        "site_social_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "settings_id",
            sa.Integer(),
            sa.ForeignKey("site_settings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", social_type_enum, nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("label", sa.String(length=80), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_index("ix_social_settings_order", "site_social_links", ["settings_id", "sort_order"])
    op.create_index("ix_site_social_links_settings_id", "site_social_links", ["settings_id"])
    op.create_index("ix_site_social_links_type", "site_social_links", ["type"])


def downgrade():
    op.drop_index("ix_site_social_links_type", table_name="site_social_links")
    op.drop_index("ix_site_social_links_settings_id", table_name="site_social_links")
    op.drop_index("ix_social_settings_order", table_name="site_social_links")

    op.drop_table("site_social_links")
    op.drop_table("site_settings")

    # Drop enum safely if exists
    bind = op.get_bind()
    social_type_enum = postgresql.ENUM(
        "INSTAGRAM",
        "FACEBOOK",
        "X",
        "TIKTOK",
        "YOUTUBE",
        "WHATSAPP",
        "WEBSITE",
        name="socialtype",
        create_type=False,
    )
    social_type_enum.drop(bind, checkfirst=True)
