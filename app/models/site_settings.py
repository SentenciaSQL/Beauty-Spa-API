from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, Boolean, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base

class SiteSettings(Base):
    __tablename__ = "site_settings"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Branding
    app_name: Mapped[str] = mapped_column(String(120), default="Spa App")
    tagline: Mapped[str | None] = mapped_column(String(160), nullable=True)  # opcional
    logo_main_url: Mapped[str | None] = mapped_column(String(500), nullable=True)      # header
    logo_sidebar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)   # sidebar/admin
    logo_small_url: Mapped[str | None] = mapped_column(String(500), nullable=True)     # favicon-ish / mobile

    # Contacto
    whatsapp_phone_e164: Mapped[str | None] = mapped_column(String(30), nullable=True)  # +1809...
    contact_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(150), nullable=True)

    # Ubicación / mapa
    address_text: Mapped[str | None] = mapped_column(String(250), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)   # precisión
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    google_maps_iframe: Mapped[str | None] = mapped_column(Text, nullable=True)     # iframe embed

    # Contenido
    about_text: Mapped[str | None] = mapped_column(Text, nullable=True)             # "Acerca de"
    terms_text: Mapped[str | None] = mapped_column(Text, nullable=True)             # opcional
    privacy_text: Mapped[str | None] = mapped_column(Text, nullable=True)           # opcional

    # Estado
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                                                 onupdate=lambda: datetime.now(timezone.utc))

    social_links: Mapped[list["SiteSocialLink"]] = relationship(
        "SiteSocialLink",
        back_populates="settings",
        cascade="all, delete-orphan",
        order_by="SiteSocialLink.sort_order.asc()",
    )
