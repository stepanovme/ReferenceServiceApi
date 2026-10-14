from fastapi import APIRouter, Depends, HTTPException

from app.database import DbSession
from app.middleware.auth_middleware import get_session
from app.services.checko_client import CheckoError
from app.services.counterparty_check_service import (
    CounterpartyCheckService,
    CounterpartyInnMissing,
    CounterpartyNotFound,
)

checks_router = APIRouter(
    prefix="/counterparties",
    tags=["Проверка контрагентов"],
    dependencies=[Depends(get_session)],
)


@checks_router.get("/checks/status", summary="Статус проверок всех контрагентов (ООО/ИП)")
def checks_status(db: DbSession):
    return CounterpartyCheckService(db).list_status()


@checks_router.post("/checks/run-due", summary="Проверить всех, у кого проверка просрочена (>1 года)")
def run_due_checks(db: DbSession):
    return CounterpartyCheckService(db).run_due()


@checks_router.get("/checks/{check_id}", summary="Отчёт по проверке")
def get_check(check_id: str, db: DbSession):
    data = CounterpartyCheckService(db).get_check(check_id)
    if not data:
        raise HTTPException(status_code=404, detail="Проверка не найдена")
    return data


@checks_router.get("/checks/{check_id}/sources", summary="Сырые данные внешних API по проверке")
def get_check_sources(check_id: str, db: DbSession):
    data = CounterpartyCheckService(db).get_raw_sources(check_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Проверка не найдена")
    return data


@checks_router.post("/{counterparty_id}/checks", summary="Запустить проверку контрагента")
def run_check(counterparty_id: str, db: DbSession):
    try:
        return CounterpartyCheckService(db).run_check(counterparty_id)
    except CounterpartyNotFound:
        raise HTTPException(status_code=404, detail="Контрагент не найден") from None
    except CounterpartyInnMissing:
        raise HTTPException(status_code=400, detail="У контрагента не указан ИНН") from None
    except CheckoError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from None


@checks_router.get("/{counterparty_id}/checks", summary="История проверок контрагента")
def list_checks(counterparty_id: str, db: DbSession):
    return CounterpartyCheckService(db).list_checks(counterparty_id)


@checks_router.get("/{counterparty_id}/checks/latest", summary="Последний отчёт по контрагенту")
def latest_check(counterparty_id: str, db: DbSession):
    data = CounterpartyCheckService(db).get_latest(counterparty_id)
    if not data:
        raise HTTPException(status_code=404, detail="Проверок ещё не было")
    return data
