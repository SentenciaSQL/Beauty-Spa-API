from fastapi import APIRouter
from app.api.v1 import auth, services, appointments, products, cash, users, availability, public, admin_whatsapp_debug, slides, gallery

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router, tags=["auth"])
router.include_router(users.router, tags=["users"])
router.include_router(services.router, tags=["services"])
router.include_router(products.router, tags=["products"])
router.include_router(appointments.router, tags=["appointments"])
router.include_router(cash.router, tags=["cash"])
router.include_router(availability.router, tags=["availability"])
router.include_router(slides.router, tags=["slides"])
router.include_router(gallery.router, tags=["gallery"])
router.include_router(public.router)
router.include_router(admin_whatsapp_debug.router)
