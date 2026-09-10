#!/usr/bin/env python3

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_url import (  # noqa: E402
    MAX_STATUS_ID,
    build_url,
    validate_handle,
    validate_query,
    validate_status_id,
    validate_status_url,
)


class BuildUrlTests(unittest.TestCase):
    def test_home(self) -> None:
        self.assertEqual(build_url("home"), "https://x.com/home")

    def test_search_builds_top_and_latest_routes(self) -> None:
        self.assertEqual(
            build_url("search", query='"node.js" OR from:example', tab="top"),
            "https://x.com/search?q=%22node.js%22%20OR%20from%3Aexample&f=top",
        )
        self.assertEqual(
            build_url("search", query="#opensource -filter:replies", tab="latest"),
            "https://x.com/search?q=%23opensource%20-filter%3Areplies&f=live",
        )

    def test_search_requires_an_explicit_supported_tab(self) -> None:
        for tab in (None, "live", "recent"):
            with self.subTest(tab=tab), self.assertRaises(ValueError):
                build_url("search", query="example", tab=tab)

    def test_query_rejects_empty_long_and_control_input(self) -> None:
        values = ("", "   ", "hello\nworld", "hello\x7fworld", "a\u00a0b", "x" * 513)
        for value in values:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_query(value)

    def test_query_preserves_x_grammar_and_unicode(self) -> None:
        query = '  (python OR "node.js") lang:en 🚀  '
        self.assertEqual(validate_query(query), '(python OR "node.js") lang:en 🚀')

    def test_profile_normalizes_handle(self) -> None:
        self.assertEqual(
            build_url("profile", handle="@Example_42"), "https://x.com/example_42"
        )

    def test_handle_rejects_invalid_and_reserved_values(self) -> None:
        values = (
            "",
            "@",
            "@@valid",
            "has-hyphen",
            "sixteen_chars_ok",
            "https://x.com/user",
            "search",
            "HOME",
        )
        for value in values:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_handle(value)

    def test_status_route_validates_unsigned_64_bit_id(self) -> None:
        self.assertEqual(
            build_url("status", handle="Example", status_id="123456789"),
            "https://x.com/example/status/123456789",
        )
        self.assertEqual(validate_status_id(str(MAX_STATUS_ID)), str(MAX_STATUS_ID))
        for value in ("", "0", "01", "-1", "+1", "1.0", str(MAX_STATUS_ID + 1)):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_status_id(value)

    def test_status_url_returns_clean_canonical_permalink(self) -> None:
        self.assertEqual(
            validate_status_url("https://x.com/Example_42/status/123456789"),
            "https://x.com/example_42/status/123456789",
        )

    def test_status_url_rejects_wrong_host_or_non_https(self) -> None:
        values = (
            "http://x.com/user/status/123",
            "https://www.x.com/user/status/123",
            "https://twitter.com/user/status/123",
            "https://x.com.evil.test/user/status/123",
            "https://x.com@evil.test/user/status/123",
            "https://user@x.com/user/status/123",
            "https://x.com:443/user/status/123",
        )
        for value in values:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_status_url(value)

    def test_status_url_rejects_extra_path_query_fragment_or_space(self) -> None:
        values = (
            "https://x.com/user/status/123/",
            "https://x.com/user/status/123/photo/1",
            "https://x.com/user/status/123?s=20",
            "https://x.com/user/status/123?",
            "https://x.com/user/status/123#fragment",
            "https://x.com/user/status/123#",
            "https://x.com/i/status/123",
            " https://x.com/user/status/123",
            "\x00https://x.com/user/status/123",
            "https://x.com/us\ter/status/123",
            "https://x.com/us\ner/status/123",
            "https://x.com/us\rer/status/123",
            "https://x.co\tm/user/status/123",
        )
        for value in values:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_status_url(value)

    def test_status_url_rejects_encoded_or_invalid_components(self) -> None:
        values = (
            "https://x.com/us%65r/status/123",
            "https://x.com/user/status/%31%32%33",
            "https://x.com/user-name/status/123",
            "https://x.com/user/status/0",
        )
        for value in values:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_status_url(value)

    def test_rejects_unknown_route(self) -> None:
        with self.assertRaises(ValueError):
            build_url("notifications")

    def test_cli_rejects_abbreviated_routes_and_options(self) -> None:
        script = Path(__file__).with_name("build_url.py")
        cases = (
            ("sear", "--query", "example", "--tab", "top"),
            ("search", "--q", "example", "--tab", "top"),
            ("search", "--query", "example", "--ta", "top"),
            ("profile", "--ha", "example"),
            ("status", "--handle", "example", "--status", "123"),
            ("validate-status-url", "--u", "https://x.com/user/status/123"),
        )
        for args in cases:
            with self.subTest(args=args):
                result = subprocess.run(
                    [sys.executable, str(script), *args],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
