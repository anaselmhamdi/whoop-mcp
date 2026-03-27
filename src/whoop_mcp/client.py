from __future__ import annotations

import httpx

BASE_URL = "https://api.prod.whoop.com/developer"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"


class WhoopAuthError(Exception):
    """Raised when authentication fails and cannot be recovered."""


class WhoopRateLimitError(Exception):
    """Raised when the WHOOP API rate limit is exceeded."""


class WhoopAPIError(Exception):
    """Raised for unexpected WHOOP API errors."""


class WhoopClient:
    """Async HTTP client for the WHOOP API with automatic token refresh."""

    def __init__(
        self,
        access_token: str,
        refresh_token: str,
        client_id: str,
        client_secret: str,
    ) -> None:
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.client_secret = client_secret
        self._http = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)

    async def close(self) -> None:
        await self._http.aclose()

    # --- public helpers ---

    async def get(self, path: str, params: dict | None = None) -> dict:
        """GET request with automatic token refresh on 401."""
        response = await self._request(path, params)

        if response.status_code == 401:
            await self.refresh_access_token()
            response = await self._request(path, params)

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

    async def refresh_access_token(self) -> None:
        """Exchange the refresh token for a new access token."""
        response = await self._http.post(
            TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
            },
        )

        if response.status_code != 200:
            raise WhoopAuthError(
                f"Token refresh failed ({response.status_code}): {response.text}"
            )

        body = response.json()
        self.access_token = body["access_token"]
        self.refresh_token = body.get("refresh_token", self.refresh_token)

    # --- internal ---

    async def _request(self, path: str, params: dict | None = None) -> httpx.Response:
        return await self._http.get(
            path,
            params=params,
            headers={"Authorization": f"Bearer {self.access_token}"},
        )

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
