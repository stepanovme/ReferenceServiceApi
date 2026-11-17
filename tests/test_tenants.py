import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from starlette.requests import Request

from app import database


def request(host, origin=None, referer=None):
    headers = [(b"host", host.encode())]
    if origin is not None:
        headers.append((b"origin", origin.encode()))
    if referer is not None:
        headers.append((b"referer", referer.encode()))
    return Request({"type": "http", "scheme": "https", "path": "/", "headers": headers})


class TenantTests(unittest.TestCase):
    def test_configuration_and_routing(self):
        env = {
            "TENANTS": "FIRST,EFIMOV", "TENANT_FIRST_HOSTS": "supply.st29.ru,metal.st29.ru,timetrack.st29.ru",
            "TENANT_FIRST_DB_NAME": "auth_first", "TENANT_FIRST_REFERENCE_DB_NAME": "reference_first",
            "TENANT_FIRST_SUPPLY_DB_NAME": "supply_first", "TENANT_EFIMOV_HOSTS": "efimov.st29.ru",
            "TENANT_EFIMOV_DB_NAME": "auth_second", "TENANT_EFIMOV_REFERENCE_DB_NAME": "reference_second",
            "TENANT_EFIMOV_SUPPLY_DB_NAME": "supply_second",
        }
        with patch.dict(os.environ, env), patch.object(database, "_engine", side_effect=lambda prefix, name: name):
            configured = database._load_tenants()
        with patch.object(database, "tenants", configured):
            first = database.get_tenant(request("api.st29.ru", "https://supply.st29.ru"))
            second = database.get_tenant(request("efimov.st29.ru:443"))
            self.assertEqual(database.get_tenant(request("timetrack.st29.ru", referer="https://timetrack.st29.ru/home")).name, "FIRST")
            self.assertEqual(database.get_tenant(request("api.st29.ru", referer="https://efimov.st29.ru/employees?tab=internal")).name, "EFIMOV")
            self.assertEqual(database.get_tenant(request("api.st29.ru", referer="https://supply.st29.ru/")).name, "FIRST")
            self.assertEqual((first.reference_engine, first.auth_engine, first.supply_engine),
                             ("reference_first", "auth_first", "supply_first"))
            self.assertEqual((second.reference_engine, second.auth_engine, second.supply_engine),
                             ("reference_second", "auth_second", "supply_second"))
            for origin in ("https://unknown.st29.ru", "null", "https://supply.st29.ru.evil.com"):
                with self.assertRaises(HTTPException):
                    database.get_tenant(request("supply.st29.ru", origin))
            for referer in (None, "https://efimov.st29.ru.evil.com/", "https://efimov.st29.ru@evil.com/"):
                with self.assertRaises(HTTPException):
                    database.get_tenant(request("api.st29.ru", referer=referer))

    def test_duplicate_hosts_rejected(self):
        env = {"TENANTS": "A,B", "TENANT_A_HOSTS": "same.example", "TENANT_B_HOSTS": "SAME.example",
               "TENANT_A_DB_NAME": "a", "TENANT_A_REFERENCE_DB_NAME": "a", "TENANT_A_SUPPLY_DB_NAME": "a"}
        with patch.dict(os.environ, env), patch.object(database, "_engine", return_value=create_engine("sqlite://")):
            with self.assertRaises(RuntimeError):
                database._load_tenants()

    def test_sessions_use_tenant_engines(self):
        engines = [create_engine("sqlite://") for _ in range(3)]
        tenant = database.Tenant("A", set(), *engines)
        for dependency, engine in zip((database.get_db, database.get_auth_db, database.get_supply_db), engines):
            generator = dependency(tenant)
            self.assertIs(next(generator).get_bind(), engine)
            generator.close()


if __name__ == "__main__":
    unittest.main()
