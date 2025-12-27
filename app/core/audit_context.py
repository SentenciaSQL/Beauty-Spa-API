from contextvars import ContextVar

current_actor_user_id: ContextVar[int | None] = ContextVar("current_actor_user_id", default=None)
