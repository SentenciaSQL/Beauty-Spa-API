import enum
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Boolean, Enum, ForeignKey, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base

class SocialType(str, enum.Enum):
    INSTAGRAM = "INSTAGRAM"
    FACEBOOK = "FACEBOOK"
    X = "X"
    TIKTOK = "TIKTOK"
    YOUTUBE = "YOUTUBE"
    WHATSAPP = "WHATSAPP"
    WEBSITE = "WEBSITE"

class SiteSocialLink(Base):
    __tablename__ = "site_social_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    settings_id: Mapped[int] = mapped_column(ForeignKey("site_settings.id", ondelete="CASCADE"), index=True)

    type: Mapped[SocialType] = mapped_column(Enum(SocialType), index=True)
    url: Mapped[str] = mapped_column(String(500))
    label: Mapped[str | None] = mapped_column(String(80), nullable=True)  # opcional: "Instagram"
    sort_order: Mapped[int] = mapped_column(Integer, default=0, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    settings: Mapped["SiteSettings"] = relationship("SiteSettings", back_populates="social_links")

    __table_args__ = (
        Index("ix_social_settings_order", "settings_id", "sort_order"),
    )
