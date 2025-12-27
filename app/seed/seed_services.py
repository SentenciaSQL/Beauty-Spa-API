from sqlalchemy.orm import Session
from app.models.service import Service

DEFAULT_SERVICES = [
    ("Hydralips (Hidratación de labios)", 45, 1800.00),
    ("Faciales", 60, 2200.00),
    ("Microneedling (Dermapen)", 90, 4500.00),
    ("Peeling", 60, 3000.00),
    ("Blanqueamientos", 60, 2500.00),
    ("Vajacial", 60, 3500.00),
    ("Micropigmentación de labios", 120, 9000.00),
    ("Tintado", 30, 1200.00),
    ("Laminado de cejas", 60, 2000.00),
    ("Pestañas", 90, 3800.00),
    ("Masaje descontracturante", 60, 3000.00),
    ("Masaje relajante", 60, 2800.00),
    ("Depilación con cera", 45, 1500.00),
]

def seed_services(db: Session):
    existing = {s.name for s in db.query(Service).all()}
    created = 0

    for name, minutes, price in DEFAULT_SERVICES:
        if name in existing:
            continue
        db.add(Service(name=name, duration_minutes=minutes, price=price, is_active=True))
        created += 1

    db.commit()
    return created
