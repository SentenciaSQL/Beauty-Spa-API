from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.db import SessionLocal
from app.core.security import hash_password
from app.models.user import User, Role

# ⚠️ Usa emails válidos (no .local) para evitar problemas con EmailStr
DEFAULT_CUSTOMERS = [
    {
        "email": "ana.perez@gmail.com",
        "first_name": "Ana",
        "last_name": "Pérez",
        "password": "Customer123!",
    },
    {
        "email": "maria.gomez@gmail.com",
        "first_name": "María",
        "last_name": "Gómez",
        "password": "Customer123!",
    },
    {
        "email": "laura.fernandez@gmail.com",
        "first_name": "Laura",
        "last_name": "Fernández",
        "password": "Customer123!",
    },
    {
        "email": "carla.rodriguez@gmail.com",
        "first_name": "Carla",
        "last_name": "Rodríguez",
        "password": "Customer123!",
    },
]

def upsert_customer(db: Session, *, email: str, first_name: str, last_name: str, password: str):
    existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if existing:
        # Mantiene el seed idempotente
        existing.first_name = first_name
        existing.last_name = last_name
        existing.role = Role.CUSTOMER
        existing.is_active = True
        db.commit()
        db.refresh(existing)
        return existing, False

    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        hashed_password=hash_password(password),
        role=Role.CUSTOMER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, True

def main():
    db = SessionLocal()
    try:
        created = 0
        for c in DEFAULT_CUSTOMERS:
            user, was_created = upsert_customer(db, **c)
            created += 1 if was_created else 0
            print(
                f"{'CREATED' if was_created else 'EXISTS '} | "
                f"{user.id:>3} | CUSTOMER | {user.email}"
            )

        print(f"\nSeed complete. New customers created: {created}")
        print("\nLogin creds (dev):")
        for c in DEFAULT_CUSTOMERS:
            print(f" - {c['email']} / {c['password']}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
