from starlette.middleware.base import BaseHTTPMiddleware
from app.core.audit_context import current_actor_user_id

class AuditActorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # actor por defecto = None
        token = current_actor_user_id.set(None)
        try:
            response = await call_next(request)

            # si alguien seteó request.state.user_id, lo copiamos al ContextVar
            actor_id = getattr(request.state, "user_id", None)
            if actor_id is not None:
                current_actor_user_id.set(int(actor_id))

            return response
        finally:
            current_actor_user_id.reset(token)

