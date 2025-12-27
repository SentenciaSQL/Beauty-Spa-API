from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal
from enum import Enum as PyEnum
from uuid import UUID

from sqlalchemy import event
from sqlalchemy.orm import Mapper, object_session
from sqlalchemy.inspection import inspect

from app.core.audit_context import current_actor_user_id
from app.models.audit_log import AuditLog
from app.models.service import Service
from app.models.product import Product
from app.models.cash import CashEntry

AUDITED_MODELS = (Service, Product, CashEntry)

def _json_safe(value):
    if value is None:
        return None

    # Decimal (Postgres Numeric) -> float (o str si prefieres exactitud)
    if isinstance(value, Decimal):
        return float(value)

    # datetime/date -> ISO string
    if isinstance(value, (datetime, date)):
        return value.isoformat()

    # Enum -> value
    if isinstance(value, PyEnum):
        return value.value

    # UUID -> str
    if isinstance(value, UUID):
        return str(value)

    # bytes -> base64? (por ahora str)
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", errors="ignore")

    # dict/list -> recursivo
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]

    # tipos simples
    if isinstance(value, (str, int, float, bool)):
        return value

    # fallback (evita crash)
    return str(value)


def _to_dict(obj) -> dict:
    insp = inspect(obj)
    data = {}
    for attr in insp.mapper.column_attrs:
        key = attr.key
        val = getattr(obj, key, None)
        data[key] = _json_safe(val)
    return data


def _changed_fields(obj) -> dict:
    insp = inspect(obj)
    changes = {}
    for attr in insp.mapper.column_attrs:
        hist = insp.attrs[attr.key].history
        if hist.has_changes():
            before = hist.deleted[0] if hist.deleted else None
            after = hist.added[0] if hist.added else getattr(obj, attr.key, None)
            changes[attr.key] = {
                "before": _json_safe(before),
                "after": _json_safe(after),
            }
    return changes

def _get_actor_id_from_target(target) -> int | None:
    sess = object_session(target)
    if sess is None:
        return None
    return sess.info.get("actor_user_id")

def _create_audit(mapper: Mapper, connection, target, action: str):
    actor_id = _get_actor_id_from_target(target) or current_actor_user_id.get()

    # para UPDATE guardamos “solo cambios” en before/after
    if action == "UPDATE":
        changes = _changed_fields(target)
        if not changes:
            return  # nada que auditar
        before = {k: v["before"] for k, v in changes.items()}
        after = {k: v["after"] for k, v in changes.items()}
    elif action == "INSERT":
        before = None
        after = _to_dict(target)
    else:  # DELETE
        before = _to_dict(target)
        after = None

    # record_id debe existir; en INSERT puede que aún no esté,
    # pero normalmente ya está si se hizo flush antes del commit.
    record_id = getattr(target, "id", None) or 0

    row = {
        "table_name": target.__tablename__,
        "record_id": record_id,
        "action": action,
        "actor_user_id": actor_id,
        "before": before,
        "after": after,
    }
    connection.execute(AuditLog.__table__.insert().values(**row))

def register_audit_listeners():
    for model in AUDITED_MODELS:
        event.listen(model, "after_insert", lambda m, c, t, a="INSERT": _create_audit(m, c, t, a))
        event.listen(model, "after_update", lambda m, c, t, a="UPDATE": _create_audit(m, c, t, a))
        event.listen(model, "after_delete", lambda m, c, t, a="DELETE": _create_audit(m, c, t, a))
