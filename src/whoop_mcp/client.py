from __future__ import annotations

import httpx

BASE_URL = "https://api.prod.whoop.com/developer"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"


class WhoopRateLimitError(Exception):
    """Raised when the WHOOP API rate limit is exceeded."""


class WhoopAPIError(Exception):
    """Raised for unexpected WHOOP API errors."""


class WhoopClient:
    """Async HTTP client for the WHOOP API."""

    def __init__(self, access_token: str) -> None:
        self.access_token = access_token
        self._http = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)

    async def close(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> WhoopClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    async def get(self, path: str, params: dict | None = None) -> dict:
        """GET request with Bearer auth."""
        response = await self._http.get(
            path,
            params=params,
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        self._raise_for_status(response)
        return response.json()

    async def get_paginated(
        self, path: str, params: dict | None = None
    ) -> list[dict]:
        """Fetch all pages for a list endpoint and return combined records."""
        params = dict(params or {})
        records: list[dict] = []

        while True:
            data = await self.get(path, params)
            records.extend(data.get("records", []))

            next_token = data.get("next_token")
            if not next_token:
                break
            params["nextToken"] = next_token

        return records

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        if response.status_code == 429:
            remaining = response.headers.get("X-RateLimit-Remaining", "?")
            reset = response.headers.get("X-RateLimit-Reset", "?")
            raise WhoopRateLimitError(
                f"Rate limit exceeded. Remaining: {remaining}, resets in {reset}s."
            )
        if response.status_code >= 400:
            raise WhoopAPIError(
                f"WHOOP API error {response.status_code}: {response.text}"
            )
