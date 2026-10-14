from __future__ import annotations

import os

import httpx

CHECKO_BASE_URL = "https://api.checko.ru/v2"
MAX_PAGES = 5

# имя источника -> (endpoint, дополнительные параметры, ключ с постраничной выдачей)
SOURCES: dict[str, tuple[str, dict, bool]] = {
    "reliability": ("reliability", {}, False),
    "finances": ("finances", {}, False),
    "legal_cases": ("legal-cases", {}, True),
    "enforcements": ("enforcements", {}, True),
    "bankruptcy": ("bankruptcy-messages", {}, True),
    "inspections": ("inspections", {"sort": "-date", "limit": 10}, True),
    "fedresurs": ("fedresurs", {}, True),
}


class CheckoError(Exception):
    pass


class CheckoClient:
    def __init__(self, api_key: str | None = None, timeout: float = 30.0) -> None:
        self.api_key = api_key or os.getenv("CHECKO_API_KEY")
        if not self.api_key:
            raise CheckoError("CHECKO_API_KEY не задан")
        self._client = httpx.Client(base_url=CHECKO_BASE_URL, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def _get(self, endpoint: str, params: dict) -> dict:
        try:
            response = self._client.get(f"/{endpoint}", params={"key": self.api_key, **params})
            response.raise_for_status()
            body = response.json()
        except httpx.HTTPError as exc:
            # не используем str(exc): в нём может оказаться URL с ключом
            raise CheckoError(f"{type(exc).__name__} при запросе {endpoint}") from None
        except ValueError:
            raise CheckoError(f"Некорректный JSON в ответе {endpoint}") from None
        meta = body.get("meta") or {}
        if meta.get("status") == "error":
            raise CheckoError(meta.get("message") or f"Ошибка Checko в {endpoint}")
        return body

    def fetch(self, source: str, inn: str) -> dict:
        endpoint, extra, paged = SOURCES[source]
        params = {"inn": inn, **extra}
        body = self._get(endpoint, params)
        data = body.get("data")
        if paged and isinstance(data, dict):
            pages = int(data.get("СтрВсего") or 1)
            for page in range(2, min(pages, MAX_PAGES) + 1):
                next_data = (self._get(endpoint, {**params, "page": page}).get("data")) or {}
                data.setdefault("Записи", []).extend(next_data.get("Записи") or [])
            data["СтрТекущ"] = 1
        return body
