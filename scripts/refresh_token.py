#!/usr/bin/env python3
"""Refresh a WHOOP access token and print the new credentials."""

from __future__ import annotations

import os
import sys

import httpx
from dotenv import load_dotenv

TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"


def main() -> None:
    load_dotenv()

    client_id = os.environ.get("WHOOP_CLIENT_ID")
    client_secret = os.environ.get("WHOOP_CLIENT_SECRET")
    refresh_token = os.environ.get("WHOOP_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        print(
            "Error: WHOOP_CLIENT_ID, WHOOP_CLIENT_SECRET, and WHOOP_REFRESH_TOKEN "
            "must be set (via environment or .env file).",
            file=sys.stderr,
        )
        sys.exit(1)

    response = httpx.post(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
        },
    )

    if response.status_code != 200:
        print(f"Token refresh failed ({response.status_code}): {response.text}", file=sys.stderr)
        sys.exit(1)

    body = response.json()
    print(f"WHOOP_ACCESS_TOKEN={body['access_token']}")
    print(f"WHOOP_REFRESH_TOKEN={body.get('refresh_token', refresh_token)}")


if __name__ == "__main__":
    main()
