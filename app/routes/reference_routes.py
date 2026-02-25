from fastapi import APIRouter, Depends, HTTPException

from app.database import AuthDbSession, DbSession
from app.middleware.auth_middleware import get_session
from app.schemas import (
    BankAccountCreate,
    ContractCreate,
    CounterpartyAdditionalCreate,
    CounterpartyCreate,
    DetailsIPCreate,
    DetailsLLCCreate,
    DetailsPhysCreate,
    EmployeeCreate,
    ObjectLevelCreate,
    ObjectCreate,
    ObjectUpdate,
    PersonCreate,
    WorkTypeCreate,
)
from app.services.reference_service import ReferenceService

base_dependencies = [Depends(get_session)]

objects_router = APIRouter(prefix="/objects", tags=["Объекты"], dependencies=base_dependencies)
persons_router = APIRouter(prefix="/persons", tags=["Лица"], dependencies=base_dependencies)
employees_router = APIRouter(prefix="/employees", tags=["Сотрудники"], dependencies=base_dependencies)
contracts_router = APIRouter(prefix="/contracts", tags=["Договоры"], dependencies=base_dependencies)
work_types_router = APIRouter(prefix="/work-types", tags=["Виды работ"], dependencies=base_dependencies)
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


@objects_router.patch("/{object_id}", summary="Редактировать объект")
def update_object(object_id: str, payload: ObjectUpdate, db: DbSession):
    service = ReferenceService(db)
    data = service.update_object(object_id, payload)
    if not data:
        raise HTTPException(status_code=404, detail="Объект не найден")
    return data


@objects_router.get("/{object_id}/levels", summary="Список уровней объекта")
def list_object_levels(object_id: str, db: DbSession):
    service = ReferenceService(db)
    return service.list_object_levels(object_id)


@objects_router.get("/{object_id}/structure", summary="Структура объекта")
def get_object_structure(object_id: str, db: DbSession):
    service = ReferenceService(db)
    data = service.get_object_structure(object_id)
    if not data:
        raise HTTPException(status_code=404, detail="Объект не найден")
    return data


@objects_router.post("/{object_id}/levels", summary="Создать уровень объекта")
def create_object_level(object_id: str, payload: ObjectLevelCreate, db: DbSession):
    service = ReferenceService(db)
    try:
        return service.create_object_level(object_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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


@employees_router.get("", summary="Список сотрудников")
def list_employees(db: DbSession):
    service = ReferenceService(db)
    return service.list_employees()


@employees_router.get("/{employee_id}/objects", summary="Объекты менеджера")
def get_employee_objects(employee_id: str, db: DbSession):
    service = ReferenceService(db)
    return service.list_objects_by_employee(employee_id)


@employees_router.get("/internal", summary="Список сотрудников по отделам")
def list_internal_employees(db: DbSession, auth_db: AuthDbSession):
    service = ReferenceService(db)
    return service.list_internal_employees(auth_db)


@employees_router.get("/internal/departments", summary="Список отделов")
def list_internal_departments(db: DbSession):
    service = ReferenceService(db)
    return service.list_internal_departments()


@employees_router.post("", summary="Создать сотрудника")
def create_employee(payload: EmployeeCreate, db: DbSession):
    service = ReferenceService(db)
    return service.create_employee(payload)


@contracts_router.get("", summary="Список договоров")
def list_contracts(db: DbSession):
    service = ReferenceService(db)
    return service.list_contracts()


@contracts_router.get("/{contract_id}", summary="Получить договор по ID")
def get_contract(contract_id: str, db: DbSession):
    service = ReferenceService(db)
    data = service.get_contract(contract_id)
    if not data:
        raise HTTPException(status_code=404, detail="Договор не найден")
    return data


@contracts_router.post("", summary="Создать договор")
def create_contract(payload: ContractCreate, db: DbSession):
    service = ReferenceService(db)
    return service.create_contract(payload)


@work_types_router.get("", summary="Список видов работ")
def list_work_types(db: DbSession):
    service = ReferenceService(db)
    return service.list_work_types()


@work_types_router.get("/{work_type_id}", summary="Получить вид работ по ID")
def get_work_type(work_type_id: str, db: DbSession):
    service = ReferenceService(db)
    data = service.get_work_type(work_type_id)
    if not data:
        raise HTTPException(status_code=404, detail="Вид работ не найден")
    return data


@work_types_router.post("", summary="Создать вид работ")
def create_work_type(payload: WorkTypeCreate, db: DbSession):
    service = ReferenceService(db)
    return service.create_work_type(payload)


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
    "/summary", summary="Сводная информация по всем контрагентам"
)
def list_counterparty_summary(db: DbSession):
    service = ReferenceService(db)
    return service.list_counterparty_summaries()


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
reference_router.include_router(contracts_router)
reference_router.include_router(work_types_router)
reference_router.include_router(counterparties_router)
