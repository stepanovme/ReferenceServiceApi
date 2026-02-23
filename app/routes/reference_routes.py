from fastapi import APIRouter, Depends, HTTPException

from app.database import DbSession
from app.middleware.auth_middleware import get_session
from app.schemas import (
    BankAccountCreate,
    CounterpartyAdditionalCreate,
    CounterpartyCreate,
    DetailsIPCreate,
    DetailsLLCCreate,
    DetailsPhysCreate,
    EmployeeCreate,
    ObjectCreate,
    PersonCreate,
)
from app.services.reference_service import ReferenceService

base_dependencies = [Depends(get_session)]

objects_router = APIRouter(prefix="/objects", tags=["Объекты"], dependencies=base_dependencies)
persons_router = APIRouter(prefix="/persons", tags=["Лица"], dependencies=base_dependencies)
employees_router = APIRouter(prefix="/employees", tags=["Сотрудники"], dependencies=base_dependencies)
counterparties_router = APIRouter(
    prefix="/counterparties",
    tags=["Контрагенты"],
    dependencies=base_dependencies,
)


@objects_router.get("", summary="Список объектов")
def list_objects(db: DbSession):
    service = ReferenceService(db)
    return service.list_objects()


@objects_router.get("/{object_id}", summary="Получить объект по ID")
def get_object(object_id: str, db: DbSession):
    service = ReferenceService(db)
    obj = service.get_object(object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Объект не найден")
    return obj


@objects_router.post("", summary="Создать объект")
def create_object(payload: ObjectCreate, db: DbSession):
    service = ReferenceService(db)
    return service.create_object(payload)


@persons_router.get("", summary="Список лиц")
def list_persons(db: DbSession, search: str | None = None):
    service = ReferenceService(db)
    return service.list_persons(search)


@persons_router.get("/{person_id}", summary="Получить лицо по ID")
def get_person(person_id: str, db: DbSession):
    service = ReferenceService(db)
    data = service.get_person(person_id)
    if not data:
        raise HTTPException(status_code=404, detail="Лицо не найдено")
    return data


@persons_router.post("", summary="Создать лицо")
def create_person(payload: PersonCreate, db: DbSession):
    service = ReferenceService(db)
    return service.create_person(payload)


@employees_router.get("/{employee_id}/objects", summary="Объекты менеджера")
def get_employee_objects(employee_id: str, db: DbSession):
    service = ReferenceService(db)
    return service.list_objects_by_employee(employee_id)


@employees_router.post("", summary="Создать сотрудника")
def create_employee(payload: EmployeeCreate, db: DbSession):
    service = ReferenceService(db)
    return service.create_employee(payload)


@counterparties_router.get("", summary="Список контрагентов")
def list_counterparties(
    db: DbSession,
    type: str | None = None,
    is_internal: bool | None = None,
):
    service = ReferenceService(db)
    return service.list_counterparties(type, is_internal)


@counterparties_router.get("/llc/{counterparty_id}", summary="ООО: детальная информация")
def get_llc(counterparty_id: str, db: DbSession):
    service = ReferenceService(db)
    data = service.get_counterparty_llc(counterparty_id)
    if not data:
        raise HTTPException(status_code=404, detail="ООО не найдено")
    return data


@counterparties_router.get("/ip/{counterparty_id}", summary="ИП: детальная информация")
def get_ip(counterparty_id: str, db: DbSession):
    service = ReferenceService(db)
    data = service.get_counterparty_ip(counterparty_id)
    if not data:
        raise HTTPException(status_code=404, detail="ИП не найден")
    return data


@counterparties_router.get("/phys/{counterparty_id}", summary="Физлицо: детальная информация")
def get_phys(counterparty_id: str, db: DbSession):
    service = ReferenceService(db)
    data = service.get_counterparty_phys(counterparty_id)
    if not data:
        raise HTTPException(status_code=404, detail="Физлицо не найдено")
    return data


@counterparties_router.get("/search", summary="Поиск контрагентов")
def search_counterparties(q: str, db: DbSession):
    service = ReferenceService(db)
    return service.search_counterparties(q)


@counterparties_router.get(
    "/{counterparty_id}/employees", summary="Сотрудники контрагента"
)
def get_counterparty_employees(counterparty_id: str, db: DbSession):
    service = ReferenceService(db)
    return service.list_counterparty_employees(counterparty_id)


@counterparties_router.get(
    "/{counterparty_id}/bank-accounts", summary="Банковские счета контрагента"
)
def get_bank_accounts(counterparty_id: str, db: DbSession):
    service = ReferenceService(db)
    return service.list_bank_accounts(counterparty_id)


@counterparties_router.get(
    "/{counterparty_id}/full-profile", summary="Полный профиль контрагента"
)
def get_full_profile(counterparty_id: str, db: DbSession):
    service = ReferenceService(db)
    data = service.get_full_profile(counterparty_id)
    if not data:
        raise HTTPException(status_code=404, detail="Контрагент не найден")
    return data


@counterparties_router.post("", summary="Создать контрагента")
def create_counterparty(payload: CounterpartyCreate, db: DbSession):
    service = ReferenceService(db)
    return service.create_counterparty(payload)


@counterparties_router.post("/llc", summary="Создать данные ООО")
def create_llc(payload: DetailsLLCCreate, db: DbSession):
    service = ReferenceService(db)
    return service.create_details_llc(payload)


@counterparties_router.post("/ip", summary="Создать данные ИП")
def create_ip(payload: DetailsIPCreate, db: DbSession):
    service = ReferenceService(db)
    return service.create_details_ip(payload)


@counterparties_router.post("/phys", summary="Создать данные физлица")
def create_phys(payload: DetailsPhysCreate, db: DbSession):
    service = ReferenceService(db)
    return service.create_details_phys(payload)


@counterparties_router.post(
    "/additional-okved", summary="Добавить дополнительный ОКВЭД"
)
def create_additional_okved(payload: CounterpartyAdditionalCreate, db: DbSession):
    service = ReferenceService(db)
    return service.create_counterparty_additional(payload)


@counterparties_router.post(
    "/{counterparty_id}/bank-accounts", summary="Создать банковский счет"
)
def create_bank_account(counterparty_id: str, payload: BankAccountCreate, db: DbSession):
    if payload.counterparty_id != counterparty_id:
        raise HTTPException(status_code=400, detail="counterparty_id не совпадает")
    service = ReferenceService(db)
    return service.create_bank_account(payload)


reference_router = APIRouter()
reference_router.include_router(objects_router)
reference_router.include_router(persons_router)
reference_router.include_router(employees_router)
reference_router.include_router(counterparties_router)
