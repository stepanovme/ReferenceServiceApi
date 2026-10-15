from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.counterparty_check import CounterpartyFileDB
from app.models.reference import CounterpartyDB

# Вне /uploads: этот каталог не раздаётся статикой, скачивание только через авторизованный эндпоинт
FILES_DIR = Path(__file__).resolve().parent.parent.parent / "counterparty_files"
MAX_FILE_SIZE = 20 * 1024 * 1024


class FileTooLarge(Exception):
    pass


def _payload(row: CounterpartyFileDB) -> dict:
    return {
        "id": row.id,
        "counterparty_id": row.counterparty_id,
        "file_name": row.file_name,
        "content_type": row.content_type,
        "size": row.size,
        "uploaded_at": row.uploaded_at,
    }


class CounterpartyFileService:
    def __init__(self, db: Session) -> None:
        self.db = db

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

        FILES_DIR.mkdir(parents=True, exist_ok=True)
        file_id = str(uuid.uuid4())
        # на диске — только uuid, без исходного имени и расширения
        (FILES_DIR / file_id).write_bytes(file_bytes)

        row = CounterpartyFileDB(
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
            self.db.query(CounterpartyFileDB)
            .filter(CounterpartyFileDB.counterparty_id == counterparty_id)
            .order_by(CounterpartyFileDB.uploaded_at.desc())
            .all()
        )
        return [_payload(r) for r in rows]

    def _get(self, counterparty_id: str, file_id: str) -> CounterpartyFileDB | None:
        return (
            self.db.query(CounterpartyFileDB)
            .filter(
                CounterpartyFileDB.id == file_id,
                CounterpartyFileDB.counterparty_id == counterparty_id,
            )
            .first()
        )

    def get_for_download(self, counterparty_id: str, file_id: str) -> tuple[Path, CounterpartyFileDB] | None:
        row = self._get(counterparty_id, file_id)
        if not row:
            return None
        path = FILES_DIR / row.stored_name
        return (path, row) if path.is_file() else None

    def delete(self, counterparty_id: str, file_id: str) -> bool:
        row = self._get(counterparty_id, file_id)
        if not row:
            return False
        path = FILES_DIR / row.stored_name
        self.db.delete(row)
        self.db.commit()
        path.unlink(missing_ok=True)
        return True
