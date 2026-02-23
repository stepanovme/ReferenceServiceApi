from fastapi import APIRouter

from app.routes.reference_routes import reference_router

main_router = APIRouter(prefix="/api/ref")

main_router.include_router(reference_router)
