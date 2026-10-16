from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Response

from app.database import DbSession
from app.middleware.auth_middleware import get_session
from app.services.counterparty_card_service import CardNotSupported, CounterpartyCardService

DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

card_router = APIRouter(
    prefix="/counterparties",
    tags=["Карточка предприятия"],
    dependencies=[Depends(get_session)],
)


@card_router.get("/{counterparty_id}/card", summary="Карточка предприятия (Word)")
def get_counterparty_card(counterparty_id: str, db: DbSession):
    try:
        result = CounterpartyCardService(db).build(counterparty_id)
    except CardNotSupported:
        raise HTTPException(status_code=400, detail="Карточка доступна только для ООО и ИП") from None
    if not result:
        raise HTTPException(status_code=404, detail="Контрагент не найден")
    content, filename = result
    return Response(
        content=content,
        media_type=DOCX_MEDIA_TYPE,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )
