import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routes import main_router
from app.services.counterparty_check_service import run_due_checks_job

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"
CHECK_INTERVAL_SECONDS = 24 * 60 * 60

logger = logging.getLogger(__name__)

init_db()


async def _annual_checks_loop():
    while True:
        try:
            await asyncio.to_thread(run_due_checks_job)
        except Exception:  # noqa: BLE001
            logger.exception("Плановая проверка контрагентов завершилась ошибкой")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(_annual_checks_loop())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(
    title="ReferenceService",
    debug=True,
    lifespan=lifespan,
)

app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.include_router(main_router)
