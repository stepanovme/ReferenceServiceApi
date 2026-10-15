from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.database import DbSession
from app.middleware.auth_middleware import get_session
from app.services.counterparty_file_service import (
    MAX_FILE_SIZE,
    CounterpartyFileService,
    FileTooLarge,
)

files_router = APIRouter(
    prefix="/counterparties",
    tags=["Файлы контрагентов"],
    dependencies=[Depends(get_session)],
)


@files_router.post("/{counterparty_id}/files", summary="Загрузить файл контрагента")
async def upload_file(
    counterparty_id: str,
    file: UploadFile,
    db: DbSession,
):
    file_bytes = await file.read(MAX_FILE_SIZE + 1)
    try:
        data = CounterpartyFileService(db).upload(
            counterparty_id,
            file.filename or "file",
            file.content_type,
            file_bytes,
        )
    except FileTooLarge:
        raise HTTPException(status_code=413, detail="Файл слишком большой (максимум 20 МБ)") from None
    if not data:
        raise HTTPException(status_code=404, detail="Контрагент не найден")
    return data


@files_router.get("/{counterparty_id}/files", summary="Список файлов контрагента")
def list_files(counterparty_id: str, db: DbSession):
    return CounterpartyFileService(db).list(counterparty_id)


@files_router.get("/{counterparty_id}/files/{file_id}", summary="Скачать файл контрагента")
def download_file(counterparty_id: str, file_id: str, db: DbSession):
    found = CounterpartyFileService(db).get_for_download(counterparty_id, file_id)
    if not found:
        raise HTTPException(status_code=404, detail="Файл не найден")
    path, row = found
    return FileResponse(
        path,
        filename=row.file_name,
        media_type=row.content_type or "application/octet-stream",
    )


@files_router.delete("/{counterparty_id}/files/{file_id}", summary="Удалить файл контрагента")
def delete_file(counterparty_id: str, file_id: str, db: DbSession):
    if not CounterpartyFileService(db).delete(counterparty_id, file_id):
        raise HTTPException(status_code=404, detail="Файл не найден")
    return {"deleted": True, "id": file_id}
