from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class ObjectCreate(BaseModel):
    id: str
    short_name: Optional[str] = None
    full_name: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = True
    manager_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CounterpartyCreate(BaseModel):
    id: str
    type: str = Field(..., description="LLC, IP, PHYSIC")
    short_name: str
    full_name: str
    is_internal: bool
    contract_prefix: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CounterpartyAdditionalCreate(BaseModel):
    counterparty_id: str
    additional_okved: str


class DetailsLLCCreate(BaseModel):
    id: int
    counterparties_id: str
    inn: str
    kpp: str
    ogrn: str
    okpo: Optional[str] = None
    okogu: Optional[str] = None
    okato: Optional[str] = None
    oktmo: Optional[str] = None
    okfs: Optional[str] = None
    okopf: Optional[str] = None
    tax_system: Optional[str] = None
    okved: Optional[str] = None
    legal_address: str
    actual_address: str
    postal_address: str
    director_person_id: str
    director_basis: Optional[str] = None
    date_register: Optional[date] = None


class DetailsIPCreate(BaseModel):
    id: int
    counterparty_id: str
    inn: str
    ogrnip: Optional[str] = None
    okpo: Optional[str] = None
    okved: Optional[str] = None
    okopf: Optional[str] = None
    okfs: Optional[str] = None
    okogu: Optional[str] = None
    okato: Optional[str] = None
    oktmo: Optional[str] = None
    person_id: str
    date_register: Optional[date] = None


class DetailsPhysCreate(BaseModel):
    counterparty_id: str
    person_id: str
    passport_series: str
    passport_number: str
    passport_issued_by: str
    passport_date_issued: date
    passport_date: date
    department_code: str
    inn: Optional[str] = None
    address_registration: str
    address_living: str


class PersonCreate(BaseModel):
    id: str
    user_id: Optional[str] = None
    name: str
    last_naem: str
    middle_name: Optional[str] = None
    phone_personal: str
    email_personal: str
    birth_date: date


class EmployeeCreate(BaseModel):
    id: str
    counterparty_id: str
    person_id: str
    position: Optional[str] = None
    phone_work: Optional[str] = None
    phone_extra: Optional[str] = None
    email_work: Optional[str] = None
    email_extra: Optional[str] = None
    role_type: str
    comment: Optional[str] = None


class BankAccountCreate(BaseModel):
    id: str
    counterparty_id: str
    bank_name: str
    bik: str
    correspondent_account: str
    account_number: str
    account_name: str
    is_treasury: bool
    is_main: bool
