from sqlalchemy.orm import Session
from app.models.business_hours import BusinessHours, BreakBlock, Weekday

def seed_business_hours(db: Session, open_time="09:00", close_time="18:00"):
    # Mon-Fri abierto; Sat/Sun cerrado (puedes cambiar)
    defaults = [
        (Weekday.MON, False),
        (Weekday.TUE, False),
        (Weekday.WED, False),
        (Weekday.THU, False),
        (Weekday.FRI, False),
        (Weekday.SAT, True),
        (Weekday.SUN, True),
    ]

    for wd, closed in defaults:
        row = db.query(BusinessHours).filter(BusinessHours.weekday == wd).one_or_none()
        if not row:
            db.add(BusinessHours(
                weekday=wd,
                open_time=open_time,
                close_time=close_time,
                is_closed=closed
            ))
        else:
            row.open_time = open_time
            row.close_time = close_time

    db.commit()

def seed_default_break(db: Session):
    # ejemplo: break lunch 13:00-14:00 L-V
    for wd in [Weekday.MON, Weekday.TUE, Weekday.WED, Weekday.THU, Weekday.FRI]:
        exists = db.query(BreakBlock).filter(
            BreakBlock.weekday == wd,
            BreakBlock.start_time == "13:00",
            BreakBlock.end_time == "14:00",
        ).one_or_none()
        if not exists:
            db.add(BreakBlock(weekday=wd, start_time="13:00", end_time="14:00", label="Lunch"))
    db.commit()
