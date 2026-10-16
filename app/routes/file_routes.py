from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import DbSession
from app.middleware.auth_middleware import get_session
from app.services.counterparty_file_service import (
    CounterpartyFileService,
    founding_documents_service,
)


def build_files_router(
    path: str,
    tag: str,
    noun: str,
    service_factory: Callable[[Session], CounterpartyFileService],
) -> APIRouter:
    """Роутер загрузки/списка/скачивания/удаления файлов контрагента по пути /{id}/<path>."""
    router = APIRouter(
        prefix="/counterparties",
        tags=[tag],
        dependencies=[Depends(get_session)],
    )

    @router.post(f"/{{counterparty_id}}/{path}", summary=f"Загрузить: {noun}")
    def upload(counterparty_id: str, file: UploadFile, db: DbSession):
        data = service_factory(db).upload(
            counterparty_id,
            file.filename or "file",
            file.content_type,
            file.file,
        )
        if not data:
            raise HTTPException(status_code=404, detail="Контрагент не найден")
        return data

    @router.get(f"/{{counterparty_id}}/{path}", summary=f"Список: {noun}")
    def list_items(counterparty_id: str, db: DbSession):
        return service_factory(db).list(counterparty_id)

    @router.get(f"/{{counterparty_id}}/{path}/{{file_id}}", summary=f"Скачать: {noun}")
    def download(counterparty_id: str, file_id: str, db: DbSession):
        found = service_factory(db).get_for_download(counterparty_id, file_id)
        if not found:
            raise HTTPException(status_code=404, detail="Файл не найден")
        file_path, row = found
        return FileResponse(
            file_path,
            filename=row.file_name,
            media_type=row.content_type or "application/octet-stream",
        )

    @router.delete(f"/{{counterparty_id}}/{path}/{{file_id}}", summary=f"Удалить: {noun}")
    def delete(counterparty_id: str, file_id: str, db: DbSession):
        if not service_factory(db).delete(counterparty_id, file_id):
            raise HTTPException(status_code=404, detail="Файл не найден")
        return {"deleted": True, "id": file_id}

    return router


files_router = build_files_router(
    "files", "Файлы контрагентов", "файл контрагента", CounterpartyFileService
)
founding_documents_router = build_files_router(
    "founding-documents",
    "Учредительные документы",
    "учредительный документ",
    founding_documents_service,
)
