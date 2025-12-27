from app.core.cache import TTLCache

# 60s por defecto. Puedes subir a 120 si quieres.
public_cache = TTLCache(ttl_seconds=60, max_items=5000)
