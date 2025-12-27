from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.db import SessionLocal
from app.core.security import hash_password
from app.models.user import User, Role


DEFAULT_USERS = [
    # ADMIN
    {
        "email": "admin@spa.com",
        "first_name": "Spa",
        "last_name": "Admin",
        "password": "Admin123!",
        "role": Role.ADMIN,
    },
    # RECEPTIONIST
    {
        "email": "reception@spa.com",
        "first_name": "Front",
        "last_name": "Desk",
        "password": "Front123!",
        "role": Role.RECEPTIONIST,
    },
    # EMPLOYEES (cosmetólogas)
    {
        "email": "sofia@spa.com",
        "first_name": "Sofía",
        "last_name": "Cosmetóloga",
        "password": "Employee123!",
        "role": Role.EMPLOYEE,
    },
    {
        "email": "valentina@spa.com",
        "first_name": "Valentina",
        "last_name": "Cosmetóloga",
        "password": "Employee123!",
        "role": Role.EMPLOYEE,
    },
]


def upsert_user(db: Session, email: str, first_name: str, last_name: str, password: str, role: Role) -> tuple[User, bool]:
    existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if existing:
        # actualiza campos básicos si quieres mantenerlo consistente
        existing.first_name = first_name
        existing.last_name = last_name
        existing.role = role
        existing.is_active = True
        # NOTA: no cambiamos password si ya existe (para no resetear sin querer)
        db.commit()
        db.refresh(existing)
        return existing, False

    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        hashed_password=hash_password(password),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, True


def main():
    db = SessionLocal()
    try:
        created_count = 0
        for u in DEFAULT_USERS:
            user, created = upsert_user(
                db=db,
                email=u["email"],
                first_name=u["first_name"],
                last_name=u["last_name"],
                password=u["password"],
                role=u["role"],
            )
            created_count += 1 if created else 0
            print(f"{'CREATED' if created else 'EXISTS '} | {user.id:>3} | {user.role.value:<12} | {user.email}")
        print(f"\nSeed complete. New users created: {created_count}")
        print("\nLogin creds (dev):")
        print(" - admin@spa.local / Admin123!")
        print(" - reception@spa.local / Front123!")
        print(" - sofia@spa.local / Employee123!")
        print(" - valentina@spa.local / Employee123!")
    finally:
        db.close()


if __name__ == "__main__":
    main()
