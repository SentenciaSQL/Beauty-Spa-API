from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy.sql import Select

def paginate(db: Session, stmt: Select, page: int, size: int):
    offset = (page - 1) * size

    # total
    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(total_stmt).scalar_one()

    # items
    items = db.execute(stmt.offset(offset).limit(size)).scalars().all()

    return items, total
