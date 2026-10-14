from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.counterparty_check import CounterpartyCheckDB, CounterpartyCheckSourceDB
from app.models.reference import CounterpartyDB, DetailsIPDB, DetailsLLCDB
from app.services.checko_client import SOURCES, CheckoClient, CheckoError

logger = logging.getLogger(__name__)

CHECK_PERIOD = timedelta(days=365)
CHECKABLE_TYPES = ("LLC", "IP")


class CounterpartyNotFound(Exception):
    pass


class CounterpartyInnMissing(Exception):
    pass


def _get_inn(db: Session, counterparty: CounterpartyDB) -> str | None:
    if counterparty.type == "LLC":
        row = (
            db.query(DetailsLLCDB.inn)
            .filter(DetailsLLCDB.counterparties_id == counterparty.id)
            .first()
        )
    elif counterparty.type == "IP":
        row = (
            db.query(DetailsIPDB.inn).filter(DetailsIPDB.counterparty_id == counterparty.id).first()
        )
    else:
        return None
    return row[0] if row and row[0] else None


def _latest_finances(data: dict | None) -> dict | None:
    if not isinstance(data, dict) or not data:
        return None
    years = sorted((y for y in data if str(y).isdigit() and isinstance(data[y], dict)), key=int)
    if not years:
        return None
    year = years[-1]
    report = data[year]

    def value(code: str):
        item = report.get(code)
        if isinstance(item, dict):
            return item.get("СумОтч", item.get("Итог"))
        return item if isinstance(item, (int, float)) else None

    return {
        "year": int(year),
        "revenue": value("2110"),
        "net_profit": value("2400"),
        "assets": value("1600"),
        "equity": value("1300"),
    }


def _records(payload: dict | None) -> list:
    data = (payload or {}).get("data")
    return (data.get("Записи") or []) if isinstance(data, dict) else []


def build_report(payloads: dict[str, dict], errors: dict[str, str], inn: str) -> dict:
    """Собирает сводный отчёт из сырых ответов Checko."""
    reliability = (payloads.get("reliability") or {}).get("data") or {}
    finances = (payloads.get("finances") or {}).get("data")
    cases = payloads.get("legal_cases")
    enforcements = _records(payloads.get("enforcements"))
    bankruptcy = _records(payloads.get("bankruptcy"))
    inspections = _records(payloads.get("inspections"))
    fedresurs = _records(payloads.get("fedresurs"))
    case_records = _records(cases)

    company = None
    for payload in payloads.values():
        company = payload.get("company") or payload.get("entrepreneur")
        if company:
            break

    balance = reliability.get("Баланс") or {}
    factors = reliability.get("Факторы") or []
    negative_factors = [f.get("Текст") for f in factors if f.get("Тип") == "Негатив"]
    attention_factors = [f.get("Текст") for f in factors if f.get("Тип") == "ТрВним"]

    inn_str = str(inn)
    defendant_cases = [
        c for c in case_records if any(str(r.get("ИНН")) == inn_str for r in c.get("Ответ") or [])
    ]
    enforcement_debt = sum(e.get("ОстЗадолж") or 0 for e in enforcements)

    report = {
        "company": company,
        "reliability": {
            "scale": reliability.get("Масштаб"),
            "nominality": reliability.get("Номинальность"),
            "financial_risks": reliability.get("ФинРиски"),
            "balance": balance or None,
            "negative_factors": negative_factors,
            "attention_factors": attention_factors,
        }
        if "reliability" in payloads
        else None,
        "finances": _latest_finances(finances) if "finances" in payloads else None,
        "legal_cases": {
            "total": ((cases or {}).get("data") or {}).get("ЗапВсего", len(case_records)),
            "total_claim_amount": ((cases or {}).get("data") or {}).get("ОбщСуммИск"),
            "active": sum(1 for c in case_records if c.get("ПрАктив")),
            "as_defendant": len(defendant_cases),
            "as_defendant_active": sum(1 for c in defendant_cases if c.get("ПрАктив")),
        }
        if "legal_cases" in payloads
        else None,
        "enforcements": {
            "total": len(enforcements),
            "total_debt": sum(e.get("СумДолг") or 0 for e in enforcements),
            "remaining_debt": enforcement_debt,
        }
        if "enforcements" in payloads
        else None,
        "bankruptcy": {
            "total": len(bankruptcy),
            "last_date": max((b.get("Дата") or "" for b in bankruptcy), default=None) or None,
        }
        if "bankruptcy" in payloads
        else None,
        "inspections": {
            "total": len(inspections),
            "with_violations": sum(1 for i in inspections if i.get("Наруш")),
        }
        if "inspections" in payloads
        else None,
        "fedresurs": {"total": len(fedresurs)} if "fedresurs" in payloads else None,
        "errors": errors,
    }

    # Эвристика итоговой оценки риска
    high = (
        bool(bankruptcy)
        or (balance.get("Негатив") or 0) >= 50
        or ((reliability.get("ФинРиски") or {}).get("Уровень") or 0) >= 4
        or ((reliability.get("Номинальность") or {}).get("Уровень") or 0) >= 3
    )
    medium = (
        bool(enforcements)
        or bool(report["legal_cases"] and report["legal_cases"]["as_defendant_active"])
        or (balance.get("Негатив") or 0) >= 20
        or ((reliability.get("ФинРиски") or {}).get("Уровень") or 0) == 3
    )
    report["risk_level"] = "high" if high else "medium" if medium else "low"
    return report


def _check_to_dict(check: CounterpartyCheckDB, with_report: bool = True) -> dict:
    data = {
        "id": check.id,
        "counterparty_id": check.counterparty_id,
        "inn": check.inn,
        "status": check.status,
        "risk_level": check.risk_level,
        "trigger": check.trigger,
        "checked_at": check.checked_at,
        "next_check_at": check.checked_at + CHECK_PERIOD,
    }
    if with_report:
        data["report"] = check.report
    return data


class CounterpartyCheckService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def run_check(self, counterparty_id: str, trigger: str = "manual") -> dict:
        counterparty = self.db.get(CounterpartyDB, counterparty_id)
        if not counterparty:
            raise CounterpartyNotFound
        inn = _get_inn(self.db, counterparty)
        if not inn:
            raise CounterpartyInnMissing

        client = CheckoClient()  # CheckoError, если нет ключа
        payloads: dict[str, dict] = {}
        errors: dict[str, str] = {}
        sources: list[CounterpartyCheckSourceDB] = []
        check_id = str(uuid.uuid4())
        try:
            for source in SOURCES:
                try:
                    payload = client.fetch(source, inn)
                    payloads[source] = payload
                    status, error = "ok", None
                except CheckoError as exc:
                    payload, status, error = None, "error", str(exc)
                    errors[source] = error
                sources.append(
                    CounterpartyCheckSourceDB(
                        check_id=check_id,
                        source=source,
                        status=status,
                        error=error,
                        payload=payload,
                        fetched_at=datetime.now(),
                    )
                )
        finally:
            client.close()

        report = build_report(payloads, errors, inn) if payloads else {"errors": errors}
        check = CounterpartyCheckDB(
            id=check_id,
            counterparty_id=counterparty_id,
            inn=inn,
            status="error" if not payloads else "partial" if errors else "ok",
            risk_level=report.get("risk_level"),
            report=report,
            trigger=trigger,
            checked_at=datetime.now(),
        )
        self.db.add(check)
        self.db.add_all(sources)
        self.db.commit()
        return _check_to_dict(check)

    def list_checks(self, counterparty_id: str) -> list[dict]:
        rows = (
            self.db.query(CounterpartyCheckDB)
            .filter(CounterpartyCheckDB.counterparty_id == counterparty_id)
            .order_by(CounterpartyCheckDB.checked_at.desc())
            .all()
        )
        return [_check_to_dict(r, with_report=False) for r in rows]

    def get_check(self, check_id: str) -> dict | None:
        check = self.db.get(CounterpartyCheckDB, check_id)
        return _check_to_dict(check) if check else None

    def get_latest(self, counterparty_id: str) -> dict | None:
        check = (
            self.db.query(CounterpartyCheckDB)
            .filter(
                CounterpartyCheckDB.counterparty_id == counterparty_id,
                CounterpartyCheckDB.status != "error",
            )
            .order_by(CounterpartyCheckDB.checked_at.desc())
            .first()
        )
        return _check_to_dict(check) if check else None

    def get_raw_sources(self, check_id: str) -> list[dict] | None:
        if not self.db.get(CounterpartyCheckDB, check_id):
            return None
        rows = (
            self.db.query(CounterpartyCheckSourceDB)
            .filter(CounterpartyCheckSourceDB.check_id == check_id)
            .all()
        )
        return [
            {
                "source": r.source,
                "status": r.status,
                "error": r.error,
                "fetched_at": r.fetched_at,
                "payload": r.payload,
            }
            for r in rows
        ]

    def list_status(self) -> list[dict]:
        """Все ООО/ИП с датой последней успешной проверки и признаком просрочки."""
        counterparties = (
            self.db.query(CounterpartyDB).filter(CounterpartyDB.type.in_(CHECKABLE_TYPES)).all()
        )
        last_checks: dict[str, CounterpartyCheckDB] = {}
        for check in (
            self.db.query(CounterpartyCheckDB)
            .filter(CounterpartyCheckDB.status != "error")
            .order_by(CounterpartyCheckDB.checked_at.asc())
            .all()
        ):
            last_checks[check.counterparty_id] = check
        now = datetime.now()
        result = []
        for cp in counterparties:
            check = last_checks.get(cp.id)
            next_at = check.checked_at + CHECK_PERIOD if check else None
            result.append(
                {
                    "counterparty_id": cp.id,
                    "short_name": cp.short_name,
                    "type": cp.type,
                    "last_checked_at": check.checked_at if check else None,
                    "risk_level": check.risk_level if check else None,
                    "next_check_at": next_at,
                    "is_due": next_at is None or next_at <= now,
                }
            )
        return result

    def run_due(self) -> dict:
        """Проверяет всех, у кого проверки не было или прошло больше года."""
        done, failed = [], {}
        for item in self.list_status():
            if not item["is_due"]:
                continue
            cp_id = item["counterparty_id"]
            try:
                self.run_check(cp_id, trigger="scheduled")
                done.append(cp_id)
            except CounterpartyInnMissing:
                failed[cp_id] = "ИНН не указан"
            except CheckoError as exc:
                failed[cp_id] = str(exc)
                break  # нет ключа — дальше нет смысла
            except Exception:  # noqa: BLE001
                logger.exception("Проверка контрагента %s не удалась", cp_id)
                self.db.rollback()
                failed[cp_id] = "внутренняя ошибка"
        return {"checked": done, "failed": failed}

