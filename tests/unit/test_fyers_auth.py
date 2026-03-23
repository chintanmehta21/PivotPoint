"""Tests for headless TOTP authentication module."""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from freezegun import freeze_time

from quant.data.fyers.auth import FyersAuth, generate_totp
from quant.data.fyers.exceptions import FyersAuthError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SECRETS = {
    "app_id": "TEST123-100",
    "secret_key": "testsecret",
    "redirect_uri": "https://trade.fyers.in/api-login/redirect-uri/abc123",
    "fyers_id": "AB01234",
    "pin": "1234",
    "totp_key": "JBSWY3DPEHPK3PXP",
}


def _write_secrets(tmp_path: Path, data: dict | None = None) -> Path:
    p = tmp_path / "secrets.json"
    p.write_text(json.dumps(data if data is not None else SECRETS))
    return p


# ---------------------------------------------------------------------------
# TestGenerateTotp
# ---------------------------------------------------------------------------


class TestGenerateTotp:
    @freeze_time("2026-01-01 00:00:00")
    def test_generates_6_digit_string(self):
        otp = generate_totp("JBSWY3DPEHPK3PXP")
        assert len(otp) == 6
        assert otp.isdigit()

    @freeze_time("2026-01-01 00:00:00")
    def test_deterministic_for_same_time(self):
        otp1 = generate_totp("JBSWY3DPEHPK3PXP")
        otp2 = generate_totp("JBSWY3DPEHPK3PXP")
        assert otp1 == otp2

    @freeze_time("2026-01-01 00:00:00")
    def test_different_keys_give_different_otps(self):
        otp1 = generate_totp("JBSWY3DPEHPK3PXP")
        otp2 = generate_totp("MFRA2YTBMJQXIZLT")
        assert otp1 != otp2

    @freeze_time("2026-01-01 00:00:00")
    def test_handles_key_with_existing_padding(self):
        """Keys that already have '=' padding should produce the same OTP."""
        otp_clean = generate_totp("JBSWY3DPEHPK3PXP")
        otp_padded = generate_totp("JBSWY3DPEHPK3PXP====")
        assert otp_clean == otp_padded


# ---------------------------------------------------------------------------
# TestFyersAuthInit
# ---------------------------------------------------------------------------


class TestFyersAuthInit:
    def test_loads_credentials(self, tmp_path):
        secrets_path = _write_secrets(tmp_path)
        auth = FyersAuth(secrets_path)
        assert auth._creds["app_id"] == "TEST123-100"
        assert auth._creds["fyers_id"] == "AB01234"

    def test_missing_file_raises(self, tmp_path):
        missing = tmp_path / "no_such_file.json"
        with pytest.raises(FileNotFoundError):
            FyersAuth(missing)

    def test_invalid_json_raises(self, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not valid json {{{")
        with pytest.raises(json.JSONDecodeError):
            FyersAuth(bad_file)


# ---------------------------------------------------------------------------
# TestFyersAuthAuthenticate
# ---------------------------------------------------------------------------


class _FakeResponse:
    """Minimal stand-in for requests.Response."""

    def __init__(self, status_code: int, body: dict):
        self.status_code = status_code
        self._body = body

    def json(self):
        return self._body


class TestFyersAuthAuthenticate:
    def _make_auth(self, tmp_path) -> FyersAuth:
        return FyersAuth(_write_secrets(tmp_path))

    def test_successful_5_step_flow(self, tmp_path):
        auth = self._make_auth(tmp_path)

        # Build mock responses in order: step1, step2, step3, step4
        step1_resp = _FakeResponse(200, {"request_key": "rk_abc"})
        step2_resp = _FakeResponse(200, {"request_key": "rk_def"})
        step3_resp = _FakeResponse(200, {"data": {"token": "session_token_xyz"}})
        step4_resp = _FakeResponse(308, {})
        step4_resp.headers = {"location": "https://cb.example.com/?auth_code=AUTHXYZ&s=ok"}

        mock_session = MagicMock()
        mock_session.post.side_effect = [step1_resp, step2_resp, step3_resp, step4_resp]

        mock_session_model = MagicMock()
        mock_session_model.generate_token.return_value = {"access_token": "ACCESS_TOKEN_123", "s": "ok"}

        with (
            patch("quant.data.fyers.auth.requests.Session", return_value=mock_session),
            patch("quant.data.fyers.auth.fyersModel.SessionModel", return_value=mock_session_model),
        ):
            token = auth.authenticate()

        assert token == "ACCESS_TOKEN_123"
        assert mock_session.post.call_count == 4
        mock_session_model.set_token.assert_called_once_with("AUTHXYZ")
        mock_session_model.generate_token.assert_called_once()

    def test_step2_failure_raises_auth_error(self, tmp_path):
        auth = self._make_auth(tmp_path)

        step1_resp = _FakeResponse(200, {"request_key": "rk_abc"})
        step2_resp = _FakeResponse(400, {"message": "invalid otp"})

        mock_session = MagicMock()
        mock_session.post.side_effect = [step1_resp, step2_resp]

        with (
            patch("quant.data.fyers.auth.requests.Session", return_value=mock_session),
            patch("quant.data.fyers.auth.fyersModel.SessionModel"),
        ):
            with pytest.raises(FyersAuthError) as exc_info:
                auth.authenticate()

        assert exc_info.value.step == 2


# ---------------------------------------------------------------------------
# TestGetValidToken
# ---------------------------------------------------------------------------


class TestGetValidToken:
    def _make_auth(self, tmp_path) -> FyersAuth:
        return FyersAuth(_write_secrets(tmp_path))

    def test_returns_cached_token_if_valid(self, tmp_path):
        auth = self._make_auth(tmp_path)
        auth._cached_token = "CACHED_TOKEN"

        mock_fyers = MagicMock()
        mock_fyers.get_profile.return_value = {"s": "ok", "data": {"name": "Test User"}}

        with patch("quant.data.fyers.auth.fyersModel.FyersModel", return_value=mock_fyers):
            token = auth.get_valid_token()

        assert token == "CACHED_TOKEN"
        # authenticate() must NOT have been called
        mock_fyers.get_profile.assert_called_once()

    def test_reauthenticates_if_expired(self, tmp_path):
        auth = self._make_auth(tmp_path)
        auth._cached_token = "EXPIRED_TOKEN"

        mock_fyers = MagicMock()
        mock_fyers.get_profile.return_value = {"s": "error", "message": "token expired"}

        with (
            patch("quant.data.fyers.auth.fyersModel.FyersModel", return_value=mock_fyers),
            patch.object(auth, "authenticate", return_value="NEW_TOKEN") as mock_auth,
        ):
            token = auth.get_valid_token()

        assert token == "NEW_TOKEN"
        mock_auth.assert_called_once()
