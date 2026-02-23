import hashlib
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session


class SessionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def is_valid(self, token: str) -> bool:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        now = datetime.now(timezone.utc)
        result = self.db.execute(
            text(
                """
                SELECT 1
                FROM sessions
                WHERE token_hash = :token_hash
                  AND expires_at > :now
                LIMIT 1
                """
            ),
            {"token_hash": token_hash, "now": now},
        ).first()
        return result is not None
