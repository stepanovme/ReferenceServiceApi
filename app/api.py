from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routes import main_router

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"

init_db()

app = FastAPI(
    title="ReferenceService",
    debug=True,
)

app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.include_router(main_router)
