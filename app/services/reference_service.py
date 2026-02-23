from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.reference import (
    BankAccountDB,
    CounterpartyAdditionalDB,
    CounterpartyDB,
    DetailsIPDB,
    DetailsLLCDB,
    DetailsPhysDB,
    EmployeeDB,
    ObjectDB,
    PersonDB,
)
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


def _full_name(person: PersonDB) -> str:
    parts = [person.last_naem, person.name, person.middle_name]
    return " ".join(part for part in parts if part)


class ReferenceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_objects(self):
        rows = (
            self.db.query(ObjectDB, EmployeeDB, PersonDB)
            .outerjoin(EmployeeDB, ObjectDB.manager_id == EmployeeDB.id)
            .outerjoin(PersonDB, EmployeeDB.person_id == PersonDB.id)
            .all()
        )
        result = []
        for obj, employee, person in rows:
            manager = None
            if employee and person:
                manager = {
                    "id": employee.id,
                    "name": person.name,
                    "last_name": person.last_naem,
                    "position": employee.position,
                }
            result.append(
                {
                    "id": obj.id,
                    "short_name": obj.short_name,
                    "full_name": obj.full_name,
                    "address": obj.address,
                    "is_active": bool(obj.is_active),
                    "manager": manager,
                    "created_at": obj.created_at,
                    "updated_at": obj.updated_at,
                }
            )
        return result

    def get_object(self, object_id: str):
        row = (
            self.db.query(ObjectDB, EmployeeDB, PersonDB)
            .outerjoin(EmployeeDB, ObjectDB.manager_id == EmployeeDB.id)
            .outerjoin(PersonDB, EmployeeDB.person_id == PersonDB.id)
            .filter(ObjectDB.id == object_id)
            .first()
        )
        if not row:
            return None
        obj, employee, person = row
        manager = None
        if employee and person:
            manager = {
                "id": employee.id,
                "name": person.name,
                "last_name": person.last_naem,
                "position": employee.position,
            }
        return {
            "id": obj.id,
            "short_name": obj.short_name,
            "full_name": obj.full_name,
            "address": obj.address,
            "is_active": bool(obj.is_active),
            "manager": manager,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
        }

    def list_counterparties(self, counterparty_type: str | None, is_internal: bool | None):
        query = self.db.query(CounterpartyDB)
        if counterparty_type:
            query = query.filter(CounterpartyDB.type == counterparty_type)
        if is_internal is not None:
            query = query.filter(CounterpartyDB.is_internal == is_internal)
        return [
            {
                "id": cp.id,
                "type": cp.type,
                "short_name": cp.short_name,
                "full_name": cp.full_name,
                "is_internal": bool(cp.is_internal),
                "contract_prefix": cp.contract_prefix,
                "created_at": cp.created_at,
            }
            for cp in query.all()
        ]

    def get_counterparty_llc(self, counterparty_id: str):
        counterparty = (
            self.db.query(CounterpartyDB)
            .filter(CounterpartyDB.id == counterparty_id, CounterpartyDB.type == "LLC")
            .first()
        )
        if not counterparty:
            return None

        details = (
            self.db.query(DetailsLLCDB)
            .filter(DetailsLLCDB.counterparties_id == counterparty_id)
            .first()
        )
        if not details:
            return None

        additional = (
            self.db.query(CounterpartyAdditionalDB.additional_okved)
            .filter(CounterpartyAdditionalDB.counterparty_id == counterparty_id)
            .all()
        )
        additional_okved = [row[0] for row in additional]

        director_person = (
            self.db.query(PersonDB)
            .filter(PersonDB.id == details.director_person_id)
            .first()
        )
        director_employee = (
            self.db.query(EmployeeDB)
            .filter(
                EmployeeDB.person_id == details.director_person_id,
                EmployeeDB.counterparty_id == counterparty_id,
            )
            .first()
        )

        director = None
        if director_person:
            director = {
                "id": director_person.id,
                "name": director_person.name,
                "last_name": director_person.last_naem,
                "middle_name": director_person.middle_name,
                "position": director_employee.position if director_employee else None,
                "phone": director_employee.phone_work if director_employee else director_person.phone_personal,
                "email": director_employee.email_work if director_employee else director_person.email_personal,
            }

        bank_accounts = (
            self.db.query(BankAccountDB)
            .filter(BankAccountDB.counterparty_id == counterparty_id)
            .all()
        )

        return {
            "id": counterparty.id,
            "basic_info": {
                "short_name": counterparty.short_name,
                "full_name": counterparty.full_name,
                "is_internal": bool(counterparty.is_internal),
                "contract_prefix": counterparty.contract_prefix,
            },
            "details": {
                "inn": details.inn,
                "kpp": details.kpp,
                "ogrn": details.ogrn,
                "okpo": details.okpo,
                "okved": details.okved,
                "tax_system": details.tax_system,
                "legal_address": details.legal_address,
                "actual_address": details.actual_address,
                "postal_address": details.postal_address,
                "date_register": details.date_register,
            },
            "additional_okved": additional_okved,
            "director": director,
            "bank_accounts": [
                {
                    "id": ba.id,
                    "bank_name": ba.bank_name,
                    "bik": ba.bik,
                    "account_number": ba.account_number,
                    "account_name": ba.account_name,
                    "is_main": bool(ba.is_main),
                    "is_treasury": bool(ba.is_treasury),
                    "correspondent_account": ba.correspondent_account,
                }
                for ba in bank_accounts
            ],
        }

    def get_counterparty_ip(self, counterparty_id: str):
        counterparty = (
            self.db.query(CounterpartyDB)
            .filter(CounterpartyDB.id == counterparty_id, CounterpartyDB.type == "IP")
            .first()
        )
        if not counterparty:
            return None

        details = (
            self.db.query(DetailsIPDB)
            .filter(DetailsIPDB.counterparty_id == counterparty_id)
            .first()
        )
        if not details:
            return None

        additional = (
            self.db.query(CounterpartyAdditionalDB.additional_okved)
            .filter(CounterpartyAdditionalDB.counterparty_id == counterparty_id)
            .all()
        )
        additional_okved = [row[0] for row in additional]

        owner_person = (
            self.db.query(PersonDB).filter(PersonDB.id == details.person_id).first()
        )

        owner = None
        if owner_person:
            owner = {
                "id": owner_person.id,
                "name": owner_person.name,
                "last_name": owner_person.last_naem,
                "middle_name": owner_person.middle_name,
                "birth_date": owner_person.birth_date,
                "phone": owner_person.phone_personal,
                "email": owner_person.email_personal,
            }

        return {
            "id": counterparty.id,
            "basic_info": {
                "short_name": counterparty.short_name,
                "full_name": counterparty.full_name,
                "is_internal": bool(counterparty.is_internal),
                "contract_prefix": counterparty.contract_prefix,
            },
            "details": {
                "inn": details.inn,
                "ogrnip": details.ogrnip,
                "okpo": details.okpo,
                "okved": details.okved,
                "okopf": details.okopf,
                "okfs": details.okfs,
                "okogu": details.okogu,
                "okato": details.okato,
                "oktmo": details.oktmo,
                "date_register": details.date_register,
            },
            "additional_okved": additional_okved,
            "owner": owner,
        }

    def get_counterparty_phys(self, counterparty_id: str):
        counterparty = (
            self.db.query(CounterpartyDB)
            .filter(CounterpartyDB.id == counterparty_id, CounterpartyDB.type == "PHYSIC")
            .first()
        )
        if not counterparty:
            return None

        details = (
            self.db.query(DetailsPhysDB)
            .filter(DetailsPhysDB.counterparty_id == counterparty_id)
            .first()
        )
        if not details:
            return None

        person = self.db.query(PersonDB).filter(PersonDB.id == details.person_id).first()
        if not person:
            return None

        employee = (
            self.db.query(EmployeeDB)
            .filter(
                EmployeeDB.counterparty_id == counterparty_id,
                EmployeeDB.person_id == details.person_id,
            )
            .first()
        )

        return {
            "id": counterparty.id,
            "basic_info": {
                "short_name": counterparty.short_name,
                "full_name": counterparty.full_name,
                "is_internal": bool(counterparty.is_internal),
            },
            "personal_data": {
                "name": person.name,
                "last_name": person.last_naem,
                "middle_name": person.middle_name,
                "birth_date": person.birth_date,
                "phone": person.phone_personal,
                "email": person.email_personal,
            },
            "passport": {
                "series": details.passport_series,
                "number": details.passport_number,
                "issued_by": details.passport_issued_by,
                "date_issued": details.passport_date_issued,
                "department_code": details.department_code,
            },
            "addresses": {
                "registration": details.address_registration,
                "living": details.address_living,
            },
            "employment": {
                "position": employee.position if employee else None,
                "phone_work": employee.phone_work if employee else None,
                "email_work": employee.email_work if employee else None,
            },
        }

    def list_persons(self, search: str | None):
        query = self.db.query(PersonDB)
        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(
                    PersonDB.name.ilike(pattern),
                    PersonDB.last_naem.ilike(pattern),
                    PersonDB.middle_name.ilike(pattern),
                    PersonDB.phone_personal.ilike(pattern),
                    PersonDB.email_personal.ilike(pattern),
                )
            )
        persons = query.all()
        if not persons:
            return []

        person_ids = [person.id for person in persons]
        employees = (
            self.db.query(EmployeeDB, CounterpartyDB)
            .join(CounterpartyDB, EmployeeDB.counterparty_id == CounterpartyDB.id)
            .filter(EmployeeDB.person_id.in_(person_ids))
            .all()
        )
        employees_by_person: dict[str, list[dict]] = {pid: [] for pid in person_ids}
        for employee, counterparty in employees:
            employees_by_person[employee.person_id].append(
                {
                    "company_id": counterparty.id,
                    "company_name": counterparty.short_name,
                    "role": employee.role_type,
                    "position": employee.position,
                }
            )

        result = []
        for person in persons:
            result.append(
                {
                    "id": person.id,
                    "name": person.name,
                    "last_name": person.last_naem,
                    "middle_name": person.middle_name,
                    "full_name": _full_name(person),
                    "phone": person.phone_personal,
                    "email": person.email_personal,
                    "birth_date": person.birth_date,
                    "companies": employees_by_person.get(person.id, []),
                }
            )
        return result

    def get_person(self, person_id: str):
        person = self.db.query(PersonDB).filter(PersonDB.id == person_id).first()
        if not person:
            return None

        employees = (
            self.db.query(EmployeeDB, CounterpartyDB)
            .join(CounterpartyDB, EmployeeDB.counterparty_id == CounterpartyDB.id)
            .filter(EmployeeDB.person_id == person_id)
            .all()
        )
        companies = [
            {
                "company_id": counterparty.id,
                "company_name": counterparty.short_name,
                "role": employee.role_type,
                "position": employee.position,
            }
            for employee, counterparty in employees
        ]

        return {
            "id": person.id,
            "name": person.name,
            "last_name": person.last_naem,
            "middle_name": person.middle_name,
            "full_name": _full_name(person),
            "phone": person.phone_personal,
            "email": person.email_personal,
            "birth_date": person.birth_date,
            "companies": companies,
        }

    def list_bank_accounts(self, counterparty_id: str):
        accounts = (
            self.db.query(BankAccountDB)
            .filter(BankAccountDB.counterparty_id == counterparty_id)
            .all()
        )
        return [
            {
                "id": account.id,
                "bank_name": account.bank_name,
                "bik": account.bik,
                "correspondent_account": account.correspondent_account,
                "account_number": account.account_number,
                "account_name": account.account_name,
                "is_treasury": bool(account.is_treasury),
                "is_main": bool(account.is_main),
            }
            for account in accounts
        ]

    def search_counterparties(self, query_text: str):
        pattern = f"%{query_text}%"
        counterparties = (
            self.db.query(CounterpartyDB)
            .outerjoin(DetailsLLCDB, DetailsLLCDB.counterparties_id == CounterpartyDB.id)
            .outerjoin(DetailsIPDB, DetailsIPDB.counterparty_id == CounterpartyDB.id)
            .outerjoin(DetailsPhysDB, DetailsPhysDB.counterparty_id == CounterpartyDB.id)
            .filter(
                or_(
                    CounterpartyDB.short_name.ilike(pattern),
                    CounterpartyDB.full_name.ilike(pattern),
                    DetailsLLCDB.inn.ilike(pattern),
                    DetailsLLCDB.ogrn.ilike(pattern),
                    DetailsIPDB.inn.ilike(pattern),
                    DetailsIPDB.ogrnip.ilike(pattern),
                    DetailsPhysDB.inn.ilike(pattern),
                )
            )
            .distinct()
            .all()
        )
        return [
            {
                "id": cp.id,
                "type": cp.type,
                "short_name": cp.short_name,
                "full_name": cp.full_name,
                "is_internal": bool(cp.is_internal),
                "contract_prefix": cp.contract_prefix,
                "created_at": cp.created_at,
            }
            for cp in counterparties
        ]

    def list_counterparty_employees(self, counterparty_id: str):
        rows = (
            self.db.query(EmployeeDB, PersonDB)
            .join(PersonDB, EmployeeDB.person_id == PersonDB.id)
            .filter(EmployeeDB.counterparty_id == counterparty_id)
            .all()
        )
        return [
            {
                "id": employee.id,
                "person_id": person.id,
                "name": person.name,
                "last_name": person.last_naem,
                "middle_name": person.middle_name,
                "position": employee.position,
                "role": employee.role_type,
                "phone_work": employee.phone_work,
                "email_work": employee.email_work,
            }
            for employee, person in rows
        ]

    def list_objects_by_employee(self, employee_id: str):
        objects = self.db.query(ObjectDB).filter(ObjectDB.manager_id == employee_id).all()
        return [
            {
                "id": obj.id,
                "short_name": obj.short_name,
                "full_name": obj.full_name,
                "address": obj.address,
                "is_active": bool(obj.is_active),
                "created_at": obj.created_at,
                "updated_at": obj.updated_at,
            }
            for obj in objects
        ]

    def get_full_profile(self, counterparty_id: str):
        counterparty = (
            self.db.query(CounterpartyDB)
            .filter(CounterpartyDB.id == counterparty_id)
            .first()
        )
        if not counterparty:
            return None

        if counterparty.type == "LLC":
            return self.get_counterparty_llc(counterparty_id)
        if counterparty.type == "IP":
            return self.get_counterparty_ip(counterparty_id)
        if counterparty.type == "PHYSIC":
            return self.get_counterparty_phys(counterparty_id)
        return None

    def create_object(self, payload: ObjectCreate):
        obj = ObjectDB(**payload.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return self.get_object(obj.id)

    def create_counterparty(self, payload: CounterpartyCreate):
        counterparty = CounterpartyDB(**payload.model_dump())
        self.db.add(counterparty)
        self.db.commit()
        self.db.refresh(counterparty)
        return {
            "id": counterparty.id,
            "type": counterparty.type,
            "short_name": counterparty.short_name,
            "full_name": counterparty.full_name,
            "is_internal": bool(counterparty.is_internal),
            "contract_prefix": counterparty.contract_prefix,
            "created_at": counterparty.created_at,
        }

    def create_details_llc(self, payload: DetailsLLCCreate):
        details = DetailsLLCDB(**payload.model_dump())
        self.db.add(details)
        self.db.commit()
        self.db.refresh(details)
        return {
            "id": details.id,
            "counterparties_id": details.counterparties_id,
        }

    def create_details_ip(self, payload: DetailsIPCreate):
        details = DetailsIPDB(**payload.model_dump())
        self.db.add(details)
        self.db.commit()
        self.db.refresh(details)
        return {
            "id": details.id,
            "counterparty_id": details.counterparty_id,
        }

    def create_details_phys(self, payload: DetailsPhysCreate):
        details = DetailsPhysDB(**payload.model_dump())
        self.db.add(details)
        self.db.commit()
        self.db.refresh(details)
        return {
            "counterparty_id": details.counterparty_id,
            "person_id": details.person_id,
        }

    def create_counterparty_additional(self, payload: CounterpartyAdditionalCreate):
        additional = CounterpartyAdditionalDB(**payload.model_dump())
        self.db.add(additional)
        self.db.commit()
        return {
            "counterparty_id": additional.counterparty_id,
            "additional_okved": additional.additional_okved,
        }

    def create_person(self, payload: PersonCreate):
        person = PersonDB(**payload.model_dump())
        self.db.add(person)
        self.db.commit()
        self.db.refresh(person)
        return self.get_person(person.id)

    def create_employee(self, payload: EmployeeCreate):
        employee = EmployeeDB(**payload.model_dump())
        self.db.add(employee)
        self.db.commit()
        self.db.refresh(employee)
        return {
            "id": employee.id,
            "counterparty_id": employee.counterparty_id,
            "person_id": employee.person_id,
            "position": employee.position,
            "phone_work": employee.phone_work,
            "email_work": employee.email_work,
            "role": employee.role_type,
        }

    def create_bank_account(self, payload: BankAccountCreate):
        account = BankAccountDB(**payload.model_dump())
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return {
            "id": account.id,
            "counterparty_id": account.counterparty_id,
            "bank_name": account.bank_name,
            "bik": account.bik,
            "correspondent_account": account.correspondent_account,
            "account_number": account.account_number,
            "account_name": account.account_name,
            "is_treasury": bool(account.is_treasury),
            "is_main": bool(account.is_main),
        }
