"""Headless TOTP-based authentication for the Fyers API.

Implements RFC 6238 TOTP generation and a 5-step login flow that does not
require browser interaction, suitable for automated / headless deployments.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import struct
import time
from pathlib import Path
from typing import Any

import requests
from fyers_apiv3 import fyersModel

from quant.data.fyers.exceptions import FyersAuthError

# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

_VAGATOR = "https://api-t2.fyers.in/vagator/v2"
_FYERS_API = "https://api.fyers.in/api/v2"


def generate_totp(key: str) -> str:
    """Return a 6-digit RFC 6238 TOTP string for *key* at the current time.

    *key* is a Base32-encoded secret (with or without trailing ``=`` padding).
    """
    # Strip any existing padding so we can re-pad correctly.
    raw_key = key.rstrip("=")
    # Base32 alphabet is 5 bits/char → pad to a multiple of 8 chars.
    padding = (8 - len(raw_key) % 8) % 8
    raw_key = raw_key + "=" * padding

    key_bytes = base64.b32decode(raw_key.upper())
    # 30-second time step (RFC 6238 default).
    counter = int(time.time()) // 30
    msg = struct.pack(">Q", counter)  # big-endian uint64

    digest = hmac.new(key_bytes, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(code % 1_000_000).zfill(6)


# ---------------------------------------------------------------------------
# FyersAuth
# ---------------------------------------------------------------------------


class FyersAuth:
    """Manages Fyers access-token lifecycle using a headless 5-step login."""

    def __init__(self, secrets_path: Path | str) -> None:
        """Load credentials from *secrets_path* (JSON file).

        Raises:
            FileNotFoundError: if the file does not exist.
            json.JSONDecodeError: if the file is not valid JSON.
        """
        secrets_path = Path(secrets_path)
        # Raises FileNotFoundError if absent.
        with secrets_path.open() as fh:
            self._creds: dict[str, Any] = json.load(fh)  # raises JSONDecodeError on bad JSON

        self._cached_token: str | None = None

    # ------------------------------------------------------------------
    # Core authentication flow
    # ------------------------------------------------------------------

    def authenticate(self) -> str:
        """Run the 5-step Fyers headless login and return a fresh access token.

        Steps
        -----
        1. ``send_login_otp_v2``   – initiate OTP dispatch (uses base64-encoded Fyers ID).
        2. ``verify_otp``          – submit TOTP; receive session ``request_key``.
        3. ``verify_pin_v2``       – submit base64-encoded PIN; receive session token.
        4. POST ``/api/v2/token``  – exchange session token for auth_code (step returns 308).
        5. ``SessionModel``        – exchange auth_code for access token via Fyers SDK.
        """
        creds = self._creds
        session = requests.Session()

        # --- Step 1: send login OTP ---
        fyers_id_b64 = base64.b64encode(creds["fyers_id"].encode()).decode()
        r1 = session.post(
            f"{_VAGATOR}/send_login_otp_v2",
            json={"fy_id": fyers_id_b64, "app_id": "2"},
        )
        if r1.status_code != 200:
            raise FyersAuthError(step=1, reason=f"HTTP {r1.status_code}: {r1.json()}")
        request_key = r1.json()["request_key"]

        # --- Step 2: verify TOTP ---
        totp = generate_totp(creds["totp_key"])
        r2 = session.post(
            f"{_VAGATOR}/verify_otp",
            json={"request_key": request_key, "otp": totp},
        )
        if r2.status_code != 200:
            raise FyersAuthError(step=2, reason=f"HTTP {r2.status_code}: {r2.json()}")
        request_key = r2.json()["request_key"]

        # --- Step 3: verify PIN ---
        pin_b64 = base64.b64encode(creds["pin"].encode()).decode()
        r3 = session.post(
            f"{_VAGATOR}/verify_pin_v2",
            json={"request_key": request_key, "identity_type": "pin", "identifier": pin_b64},
        )
        if r3.status_code != 200:
            raise FyersAuthError(step=3, reason=f"HTTP {r3.status_code}: {r3.json()}")
        session_token = r3.json()["data"]["token"]

        # --- Step 4: obtain auth_code (expect 308 redirect) ---
        r4 = session.post(
            f"{_FYERS_API}/token",
            headers={"Authorization": f"Bearer {session_token}"},
            json={
                "fyers_id": creds["fyers_id"],
                "app_id": creds["app_id"].split("-")[0],
                "redirect_uri": creds["redirect_uri"],
                "appType": creds["app_id"].split("-")[1] if "-" in creds["app_id"] else "100",
                "code_challenge": "",
                "state": "None",
                "scope": "",
                "nonce": "",
                "response_type": "code",
                "create_cookie": True,
            },
            allow_redirects=False,
        )
        if r4.status_code != 308:
            raise FyersAuthError(step=4, reason=f"Expected 308, got HTTP {r4.status_code}")
        location = r4.headers.get("location", "")
        # Parse auth_code from query string in the redirect URL.
        auth_code = _extract_query_param(location, "auth_code")
        if not auth_code:
            raise FyersAuthError(step=4, reason=f"auth_code missing in redirect: {location}")

        # --- Step 5: exchange auth_code for access token ---
        session_model = fyersModel.SessionModel(
            client_id=creds["app_id"],
            redirect_uri=creds["redirect_uri"],
            response_type="code",
            secret_key=creds["secret_key"],
            grant_type="authorization_code",
        )
        session_model.set_token(auth_code)
        token_resp = session_model.generate_token()
        access_token = token_resp["access_token"]
        self._cached_token = access_token
        return access_token

    # ------------------------------------------------------------------
    # Token lifecycle
    # ------------------------------------------------------------------

    def get_valid_token(self) -> str:
        """Return a valid access token, re-authenticating if the cached one is stale.

        Validity is checked by calling ``get_profile()`` on the Fyers API.  If
        the profile call returns ``"s": "ok"`` the cached token is still live;
        any ``ConnectionError``, ``KeyError``, or ``TypeError`` — or a non-ok
        status string — triggers a fresh ``authenticate()``.
        """
        if self._cached_token is not None:
            try:
                fyers = fyersModel.FyersModel(
                    client_id=self._creds["app_id"],
                    token=self._cached_token,
                    is_async=False,
                    log_path="",
                )
                profile = fyers.get_profile()
                if profile.get("s") == "ok":
                    return self._cached_token
            except (ConnectionError, KeyError, TypeError):
                pass  # fall through to re-auth

        self._cached_token = self.authenticate()
        return self._cached_token


# ---------------------------------------------------------------------------
# Internal utilities
# ---------------------------------------------------------------------------


def _extract_query_param(url: str, param: str) -> str | None:
    """Extract a single query-string parameter value from a URL string."""
    from urllib.parse import parse_qs, urlparse

    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    values = params.get(param)
    return values[0] if values else None
