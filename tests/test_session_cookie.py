import unittest
from unittest.mock import Mock, patch

from fastapi import HTTPException
from starlette.requests import Request

from app.database import Tenant
from app.middleware.auth_middleware import get_session


class SessionCookieTests(unittest.TestCase):
    def test_each_tenant_uses_its_own_cookie(self):
        request = Request({"type": "http", "headers": [(b"cookie", b"session=first-token; session_efimov=second-token")]})
        db = Mock()
        with patch("app.middleware.auth_middleware.SessionRepository") as repository:
            repository.return_value.is_valid.return_value = True
            first = Tenant("FIRST", set(), None, None, None)
            second = Tenant("EFIMOV", set(), None, None, None, "session_efimov")
            self.assertEqual(get_session(request, db, first), "first-token")
            self.assertEqual(get_session(request, db, second), "second-token")
            repository.return_value.is_valid.assert_called_with("second-token")

    def test_does_not_fall_back_to_other_tenant_cookie(self):
        request = Request({"type": "http", "headers": [(b"cookie", b"session=first-token")]})
        tenant = Tenant("EFIMOV", set(), None, None, None, "session_efimov")
        with self.assertRaises(HTTPException) as error:
            get_session(request, Mock(), tenant)
        self.assertEqual(error.exception.detail, "Session token missing")
