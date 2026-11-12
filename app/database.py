import os
from dataclasses import dataclass
from typing import Annotated, Generator
from urllib.parse import urlsplit

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Request
from sqlalchemy import URL, create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()


class Base(DeclarativeBase):
    pass


@dataclass
class Tenant:
    name: str
    hosts: set[str]
    reference_engine: Engine
    auth_engine: Engine
    supply_engine: Engine


def _engine(prefix: str, database: str) -> Engine:
    def setting(key: str) -> str | None:
        return os.getenv(f"{prefix}_{key}", os.getenv(f"DB_{key}")) if prefix else os.getenv(f"DB_{key}")

    return create_engine(URL.create(
        "mysql+pymysql", username=setting("USER"), password=setting("PASSWORD"),
        host=setting("HOST"), port=int(setting("PORT") or 3306), database=database,
    ))


def _required(key: str) -> str:
    value = os.getenv(key, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


def _load_tenants() -> list[Tenant]:
    names = [name.strip().upper() for name in os.getenv("TENANTS", "").split(",") if name.strip()]
    if not names:
        # Existing single-tenant installations remain usable until TENANTS is configured.
        return [Tenant("default", set(), _engine("", _required("DB_NAME")),
                       _engine("AUTH_DB", os.getenv("AUTH_DB_NAME") or _required("DB_NAME")),
                       _engine("SUPPLY_DB", os.getenv("SUPPLY_DB_NAME") or _required("DB_NAME")))]
    tenants = []
    used_hosts: set[str] = set()
    for name in names:
        prefix = f"TENANT_{name}"
        hosts = {host.strip().lower().rstrip(".") for host in _required(f"{prefix}_HOSTS").split(",") if host.strip()}
        if not hosts or used_hosts.intersection(hosts):
            raise RuntimeError(f"Empty or duplicate hosts for tenant {name}")
        used_hosts.update(hosts)
        tenants.append(Tenant(name, hosts,
                              _engine("", _required(f"{prefix}_REFERENCE_DB_NAME")),
                              _engine("AUTH_DB", _required(f"{prefix}_DB_NAME")),
                              _engine("SUPPLY_DB", _required(f"{prefix}_SUPPLY_DB_NAME"))))
    return tenants


tenants = _load_tenants()


def get_tenant(request: Request) -> Tenant:
    if len(tenants) == 1 and tenants[0].name == "default":
        return tenants[0]
    origin = request.headers.get("origin")
    try:
        parsed = urlsplit(origin) if origin else None
        if parsed and (parsed.scheme not in ("http", "https") or not parsed.hostname or
                       parsed.username or parsed.password or parsed.path not in ("", "/") or
                       parsed.query or parsed.fragment):
            raise ValueError("Invalid origin")
        host = (parsed.hostname if parsed else request.url.hostname) or ""
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request origin")
    host = host.lower().rstrip(".")
    for tenant in tenants:
        if host in tenant.hosts:
            return tenant
    raise HTTPException(status_code=400, detail="Unknown tenant host")


def _session(engine: Engine) -> Generator[Session, None, None]:
    db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        yield db
    finally:
        db.close()


def get_db(tenant: Tenant = Depends(get_tenant)) -> Generator[Session, None, None]:
    yield from _session(tenant.reference_engine)


def get_auth_db(tenant: Tenant = Depends(get_tenant)) -> Generator[Session, None, None]:
    yield from _session(tenant.auth_engine)


def get_supply_db(tenant: Tenant = Depends(get_tenant)) -> Generator[Session, None, None]:
    yield from _session(tenant.supply_engine)


def init_db():
    for tenant in tenants:
        engine = tenant.reference_engine
        Base.metadata.create_all(bind=engine)
        with engine.connect() as conn:
            for table, column, ddl in (
                ("counterparties", "logo_url", "VARCHAR(500) NULL"),
                ("details_ip", "legal_address", "TEXT NULL"),
                ("details_ip", "actual_address", "TEXT NULL"),
                ("details_ip", "postal_address", "TEXT NULL"),
            ):
                result = conn.execute(
                    text("SELECT COUNT(*) FROM information_schema.COLUMNS "
                         "WHERE TABLE_SCHEMA = DATABASE() "
                         "AND TABLE_NAME = :table AND COLUMN_NAME = :column"),
                    {"table": table, "column": column},
                )
                if result.scalar() == 0:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
                    conn.commit()


DbSession = Annotated[Session, Depends(get_db)]
AuthDbSession = Annotated[Session, Depends(get_auth_db)]
SupplyDbSession = Annotated[Session, Depends(get_supply_db)]
