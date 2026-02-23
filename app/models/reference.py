from sqlalchemy import CHAR, Boolean, Column, Date, DateTime, Integer, String, Text

from app.database import Base


class BankAccountDB(Base):
    __tablename__ = "bank_accounts"

    id = Column(CHAR(36), primary_key=True)
    counterparty_id = Column(CHAR(36), nullable=False)
    bank_name = Column(Text, nullable=False)
    bik = Column(Text, nullable=False)
    correspondent_account = Column(Text, nullable=False)
    account_number = Column(Text, nullable=False)
    account_name = Column(Text, nullable=False)
    is_treasury = Column(Boolean, nullable=False)
    is_main = Column(Boolean, nullable=False)


class CounterpartyDB(Base):
    __tablename__ = "counterparties"

    id = Column(CHAR(36), primary_key=True)
    type = Column(String(10), nullable=False)
    short_name = Column(String(100), nullable=False)
    full_name = Column(String(200), nullable=False)
    is_internal = Column(Boolean, nullable=False)
    contract_prefix = Column(String(10))
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


class CounterpartyAdditionalDB(Base):
    __tablename__ = "counterparties_additional"

    counterparty_id = Column(String(36), primary_key=True)
    additional_okved = Column(Text, primary_key=True)


class DetailsIPDB(Base):
    __tablename__ = "details_ip"

    id = Column(Integer, primary_key=True)
    counterparty_id = Column(CHAR(36), nullable=False)
    inn = Column(String(200), nullable=False)
    ogrnip = Column(String(200))
    okpo = Column(String(200))
    okved = Column(String(200))
    okopf = Column(String(200))
    okfs = Column(String(200))
    okogu = Column(String(200))
    okato = Column(String(200))
    oktmo = Column(String(200))
    person_id = Column(CHAR(36), nullable=False)
    date_register = Column(Date)


class DetailsLLCDB(Base):
    __tablename__ = "details_llc"

    id = Column(Integer, primary_key=True)
    counterparties_id = Column(CHAR(36), nullable=False)
    inn = Column(String(50), nullable=False)
    kpp = Column(String(50), nullable=False)
    ogrn = Column(String(50), nullable=False)
    okpo = Column(String(200))
    okogu = Column(String(200))
    okato = Column(String(200))
    oktmo = Column(String(200))
    okfs = Column(String(200))
    okopf = Column(String(200))
    tax_system = Column(String(200))
    okved = Column(String(200))
    legal_address = Column(Text, nullable=False)
    actual_address = Column(Text, nullable=False)
    postal_address = Column(Text, nullable=False)
    director_person_id = Column(CHAR(36), nullable=False)
    director_basis = Column(String(100))
    date_register = Column(Date)


class DetailsPhysDB(Base):
    __tablename__ = "details_phys"

    counterparty_id = Column(CHAR(36), primary_key=True)
    person_id = Column(CHAR(36), primary_key=True)
    passport_series = Column(String(200), nullable=False)
    passport_number = Column(String(200), nullable=False)
    passport_issued_by = Column(Text, nullable=False)
    passport_date_issued = Column(Date, nullable=False)
    passport_date = Column(Date, nullable=False)
    department_code = Column(String(7), nullable=False)
    inn = Column(String(200))
    address_registration = Column(Text, nullable=False)
    address_living = Column(Text, nullable=False)


class EmployeeDB(Base):
    __tablename__ = "employees"

    id = Column(CHAR(36), primary_key=True)
    counterparty_id = Column(CHAR(36), nullable=False)
    person_id = Column(CHAR(36), nullable=False)
    position = Column(String(100))
    phone_work = Column(String(18))
    phone_extra = Column(String(18))
    email_work = Column(String(100))
    email_extra = Column(String(100))
    role_type = Column(String(20), nullable=False)
    comment = Column(Text)


class ObjectDB(Base):
    __tablename__ = "objects"

    id = Column(String(36), primary_key=True)
    short_name = Column(String(255))
    full_name = Column(String(500))
    address = Column(Text)
    is_active = Column(Boolean, default=True)
    manager_id = Column(String(36))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class PersonDB(Base):
    __tablename__ = "persons"

    id = Column(CHAR(36), primary_key=True)
    name = Column(String(100), nullable=False)
    last_naem = Column(String(100), nullable=False)
    middle_name = Column(String(100))
    phone_personal = Column(String(18), nullable=False)
    email_personal = Column(String(200), nullable=False)
    birth_date = Column(Date, nullable=False)
