"""WHOOP token verifier for FastMCP OAuthProxy.

WHOOP issues opaque tokens (not JWTs), so we validate them by calling the
WHOOP API. If the token returns a valid profile, it's valid.
"""

from __future__ import annotations

import httpx
from fastmcp.server.auth import AccessToken, TokenVerifier

from whoop_mcp.client import BASE_URL

WHOOP_SCOPES = [
    "read:profile",
    "read:body_measurement",
    "read:cycles",
    "read:recovery",
    "read:sleep",
    "read:workout",
    "offline",
]


class WhoopTokenVerifier(TokenVerifier):
    """Validates WHOOP opaque access tokens by calling the profile endpoint."""

    def __init__(self) -> None:
        super().__init__(required_scopes=WHOOP_SCOPES)

    async def verify_token(self, token: str) -> AccessToken | None:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as http:
            response = await http.get(
                "/v1/user/profile/basic",
                headers={"Authorization": f"Bearer {token}"},
            )

        if response.status_code != 200:
            return None

        data = response.json()
        return AccessToken(
            token=token,
            client_id=str(data.get("user_id", "")),
            scopes=WHOOP_SCOPES,
        )
