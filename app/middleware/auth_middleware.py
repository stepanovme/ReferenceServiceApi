from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import Tenant, get_auth_db, get_tenant
from app.repositories.session_repository import SessionRepository


def get_session(
    request: Request,
    db: Session = Depends(get_auth_db),
    tenant: Tenant = Depends(get_tenant),
):
    session_token = request.cookies.get(tenant.session_cookie)
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session token missing"
        )

    session_repository = SessionRepository(db)
    if not session_repository.is_valid(session_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    return session_token
