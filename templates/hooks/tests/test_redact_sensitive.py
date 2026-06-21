"""Tests for shared redact_sensitive hook helpers."""

from __future__ import annotations

if __name__ == "__main__":
    from _hooks_bootstrap import run_test_file, runtime_ok

    if not runtime_ok():
        raise SystemExit(run_test_file(__file__))

import json
import sys
import unittest
from io import StringIO
from unittest.mock import patch

from _hooks_bootstrap import ensure_policy_path, run_test_file

ensure_policy_path()

import redact_sensitive  # noqa: E402


class RedactSensitiveTests(unittest.TestCase):
    def test_is_sensitive_path_matches_service_account_and_pfx(self) -> None:
        self.assertTrue(redact_sensitive.is_sensitive_path("/proj/service-account.json"))
        self.assertTrue(redact_sensitive.is_sensitive_path("C:\\secrets\\prod.pfx"))
        self.assertFalse(redact_sensitive.is_sensitive_path("/proj/README.md"))

    def test_redact_text_masks_env_bearer_and_json_secrets(self) -> None:
        text = (
            "API_KEY=super-secret\n"
            'config={"access_token":"abc123","note":"ok"}\n'
            "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig\n"
        )
        redacted = redact_sensitive.redact_text(text)
        self.assertIn("API_KEY=***REDACTED***", redacted)
        self.assertIn("config=***REDACTED***", redacted)
        self.assertIn("Bearer ***REDACTED***", redacted)
        self.assertNotIn("super-secret", redacted)
        self.assertNotIn("abc123", redacted)

    def test_redact_read_payload_redacts_sensitive_path(self) -> None:
        payload = {
            "file_path": "/proj/.env",
            "content": "DB_PASSWORD=local-dev-secret\n",
        }
        result = redact_sensitive.redact_read_payload(payload)
        self.assertEqual(result["permission"], "allow")
        self.assertIn("***REDACTED***", result["content"])
        self.assertNotIn("local-dev-secret", result["content"])

    def test_redact_read_payload_redacts_secrets_in_plain_paths(self) -> None:
        payload = {
            "file_path": "/proj/config/app.json",
            "content": '{"api_key":"leaked-value"}',
        }
        result = redact_sensitive.redact_read_payload(payload)
        self.assertIn("***REDACTED***", result["content"])
        self.assertNotIn("leaked-value", result["content"])

    def test_main_redact_read_payload_roundtrip(self) -> None:
        payload = {"file_path": "token.json", "content": "TOKEN=abc\n"}
        stdin = json.dumps(payload)
        with patch.object(sys, "argv", ["redact_sensitive.py", "redact-read-payload"]):
            with patch.object(sys, "stdin", StringIO(stdin)):
                buf = StringIO()
                with patch.object(sys, "stdout", buf):
                    code = redact_sensitive.main(["redact-read-payload"])
        self.assertEqual(code, 0)
        result = json.loads(buf.getvalue())
        self.assertEqual(result["permission"], "allow")
        self.assertIn("***REDACTED***", result["content"])


if __name__ == "__main__":
    raise SystemExit(run_test_file(__file__))
