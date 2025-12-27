import enum
from sqlalchemy import Enum, String, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class Weekday(int, enum.Enum):
    MON = 1
    TUE = 2
    WED = 3
    THU = 4
    FRI = 5
    SAT = 6
    SUN = 7

class BusinessHours(Base):
    __tablename__ = "business_hours"

    id: Mapped[int] = mapped_column(primary_key=True)
    weekday: Mapped[Weekday] = mapped_column(Enum(Weekday), index=True)

    open_time: Mapped[str] = mapped_column(String(5))   # "09:00"
    close_time: Mapped[str] = mapped_column(String(5))  # "18:00"
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (Index("ux_business_hours_weekday", "weekday", unique=True),)

class BreakBlock(Base):
    __tablename__ = "break_blocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    weekday: Mapped[Weekday] = mapped_column(Enum(Weekday), index=True)

    start_time: Mapped[str] = mapped_column(String(5))  # "13:00"
    end_time: Mapped[str] = mapped_column(String(5))    # "14:00"
    label: Mapped[str | None] = mapped_column(String(80), nullable=True)

    __table_args__ = (
        Index("ix_break_weekday_time", "weekday", "start_time", "end_time"),
    )
