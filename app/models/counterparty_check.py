from sqlalchemy import JSON, CHAR, Column, DateTime, Integer, String, Text

from app.database import Base


class CounterpartyCheckDB(Base):
    __tablename__ = "counterparty_checks"

    id = Column(CHAR(36), primary_key=True)
    counterparty_id = Column(CHAR(36), nullable=False, index=True)
    inn = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)  # ok | partial | error
    risk_level = Column(String(10))  # low | medium | high
    report = Column(JSON)
    trigger = Column(String(20), nullable=False)  # manual | scheduled
    checked_at = Column(DateTime, nullable=False, index=True)


class CounterpartyCheckSourceDB(Base):
    __tablename__ = "counterparty_check_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    check_id = Column(CHAR(36), nullable=False, index=True)
    source = Column(String(30), nullable=False)
    status = Column(String(10), nullable=False)  # ok | error
    error = Column(Text)
    payload = Column(JSON)
    fetched_at = Column(DateTime, nullable=False)


class CounterpartyFileDB(Base):
    __tablename__ = "counterparty_files"

    id = Column(CHAR(36), primary_key=True)
    counterparty_id = Column(CHAR(36), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    stored_name = Column(String(64), nullable=False)
    content_type = Column(String(100))
    size = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, nullable=False)
