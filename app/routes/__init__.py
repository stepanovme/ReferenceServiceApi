from fastapi import APIRouter

from app.routes.check_routes import checks_router
from app.routes.file_routes import files_router
from app.routes.reference_routes import reference_router

main_router = APIRouter(prefix="/api/ref")

main_router.include_router(reference_router)
main_router.include_router(checks_router)
main_router.include_router(files_router)
