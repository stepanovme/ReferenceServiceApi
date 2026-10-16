from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.counterparty_check import CounterpartyFileDB, CounterpartyFoundingDocumentDB
from app.models.reference import CounterpartyDB

# Вне /uploads: этот каталог не раздаётся статикой, скачивание только через авторизованный эндпоинт
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
FILES_DIR = ROOT_DIR / "counterparty_files"
FOUNDING_DOCUMENTS_DIR = ROOT_DIR / "counterparty_founding_documents"
MAX_FILE_SIZE = 20 * 1024 * 1024


class FileTooLarge(Exception):
    pass


def _payload(row) -> dict:
    return {
        "id": row.id,
        "counterparty_id": row.counterparty_id,
        "file_name": row.file_name,
        "content_type": row.content_type,
        "size": row.size,
        "uploaded_at": row.uploaded_at,
    }


class CounterpartyFileService:
    """Хранилище файлов контрагента: модель и каталог задают, какие именно файлы."""

    def __init__(
        self,
        db: Session,
        model: type = CounterpartyFileDB,
        directory: Path = FILES_DIR,
    ) -> None:
        self.db = db
        self.model = model
        self.dir = directory

    def _exists(self, counterparty_id: str) -> bool:
        return self.db.query(CounterpartyDB.id).filter(CounterpartyDB.id == counterparty_id).first() is not None

    def upload(
        self,
        counterparty_id: str,
        filename: str,
        content_type: str | None,
        file_bytes: bytes,
    ) -> dict | None:
        if not self._exists(counterparty_id):
            return None
        if len(file_bytes) > MAX_FILE_SIZE:
            raise FileTooLarge

        self.dir.mkdir(parents=True, exist_ok=True)
        file_id = str(uuid.uuid4())
        # на диске — только uuid, без исходного имени и расширения
        (self.dir / file_id).write_bytes(file_bytes)

        row = self.model(
            id=file_id,
            counterparty_id=counterparty_id,
            file_name=Path(filename).name[:255] or "file",
            stored_name=file_id,
            content_type=(content_type or None),
            size=len(file_bytes),
            uploaded_at=datetime.now(),
        )
        self.db.add(row)
        self.db.commit()
        return _payload(row)

    def list(self, counterparty_id: str) -> list[dict]:
        rows = (
            self.db.query(self.model)
            .filter(self.model.counterparty_id == counterparty_id)
            .order_by(self.model.uploaded_at.desc())
            .all()
        )
        return [_payload(r) for r in rows]

    def _get(self, counterparty_id: str, file_id: str):
        return (
            self.db.query(self.model)
            .filter(
                self.model.id == file_id,
                self.model.counterparty_id == counterparty_id,
            )
            .first()
        )

    def get_for_download(self, counterparty_id: str, file_id: str) -> tuple[Path, object] | None:
        row = self._get(counterparty_id, file_id)
        if not row:
            return None
        path = self.dir / row.stored_name
        return (path, row) if path.is_file() else None

    def delete(self, counterparty_id: str, file_id: str) -> bool:
        row = self._get(counterparty_id, file_id)
        if not row:
            return False
        path = self.dir / row.stored_name
        self.db.delete(row)
        self.db.commit()
        path.unlink(missing_ok=True)
        return True


def founding_documents_service(db: Session) -> CounterpartyFileService:
    return CounterpartyFileService(db, CounterpartyFoundingDocumentDB, FOUNDING_DOCUMENTS_DIR)
