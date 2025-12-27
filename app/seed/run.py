from app.core.db import SessionLocal
from app.seed.seed_services import seed_services
from app.seed.seed_hours import seed_business_hours, seed_default_break
from app.core.config import settings

def main():
    db = SessionLocal()
    try:
        seed_business_hours(db, open_time=settings.BUSINESS_OPEN_TIME, close_time=settings.BUSINESS_CLOSE_TIME)
        seed_default_break(db)
        created = seed_services(db)
        print(f"Seed OK. Services created: {created}. Currency={settings.CURRENCY} TZ={settings.TIMEZONE}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
