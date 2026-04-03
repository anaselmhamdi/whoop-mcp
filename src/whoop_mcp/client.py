from __future__ import annotations

from collections.abc import Callable

import httpx

BASE_URL = "https://api.prod.whoop.com/developer"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"


class WhoopRateLimitError(Exception):
    """Raised when the WHOOP API rate limit is exceeded."""


class WhoopAPIError(Exception):
    """Raised for unexpected WHOOP API errors."""


class WhoopClient:
    """Async HTTP client for the WHOOP API."""

    def __init__(
        self,
        access_token: str,
        *,
        client_id: str | None = None,
        client_secret: str | None = None,
        refresh_token: str | None = None,
        on_token_refresh: Callable[[str, str], None] | None = None,
    ) -> None:
        self.access_token = access_token
        self._client_id = client_id
        self._client_secret = client_secret
        self._refresh_token = refresh_token
        self._on_token_refresh = on_token_refresh
        self._http = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)

    @property
    def _can_refresh(self) -> bool:
        return bool(self._client_id and self._client_secret and self._refresh_token)

    async def _do_refresh(self) -> None:
        """Exchange the refresh token for a new access token."""
        async with httpx.AsyncClient(timeout=10.0) as http:
            resp = await http.post(
                TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self._refresh_token,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                },
            )
        if resp.status_code != 200:
            raise WhoopAPIError(
                f"Token refresh failed ({resp.status_code}): {resp.text}"
            )
        data = resp.json()
        self.access_token = data["access_token"]
        self._refresh_token = data.get("refresh_token", self._refresh_token)
        if self._on_token_refresh:
            self._on_token_refresh(self.access_token, self._refresh_token)

    async def close(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> WhoopClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    async def get(self, path: str, params: dict | None = None) -> dict:
        """GET request with Bearer auth. Retries once after token refresh on 401."""
        response = await self._http.get(
            path,
            params=params,
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        if response.status_code == 401 and self._can_refresh:
            await self._do_refresh()
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
