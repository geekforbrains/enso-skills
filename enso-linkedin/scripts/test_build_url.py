#!/usr/bin/env python3

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_url import build_url  # noqa: E402


class BuildUrlTests(unittest.TestCase):
    def test_feed(self) -> None:
        self.assertEqual(build_url("feed"), "https://www.linkedin.com/feed/")

    def test_me(self) -> None:
        self.assertEqual(build_url("me"), "https://www.linkedin.com/in/me/")

    def test_search_encodes_query(self) -> None:
        self.assertEqual(
            build_url("search", query="  distributed systems & Node  "),
            "https://www.linkedin.com/search/results/content/?keywords=distributed+systems+%26+Node",
        )

    def test_search_encodes_supported_sort_and_date(self) -> None:
        self.assertEqual(
            build_url(
                "search",
                query="example.js",
                sort="date-posted",
                date_posted="past-week",
            ),
            "https://www.linkedin.com/search/results/content/?keywords=example.js&sortBy=%22date_posted%22&datePosted=%22past-week%22",
        )

    def test_search_rejects_empty_or_control_characters(self) -> None:
        for value in (
            "",
            "   ",
            "hello\nworld",
            "hello\x7fworld",
            "a\x85b",
            "a\ud800b",
            "x" * 513,
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                build_url("search", query=value)

    def test_search_preserves_unicode(self) -> None:
        self.assertEqual(
            build_url("search", query="café 🚀"),
            "https://www.linkedin.com/search/results/content/?keywords=caf%C3%A9+%F0%9F%9A%80",
        )

    def test_search_rejects_unsupported_sort_or_date(self) -> None:
        with self.assertRaises(ValueError):
            build_url("search", query="example", sort="popular")
        with self.assertRaises(ValueError):
            build_url("search", query="example", date_posted="all-time")

    def test_profile_accepts_public_slug(self) -> None:
        self.assertEqual(
            build_url("profile", slug="example-member-42"),
            "https://www.linkedin.com/in/example-member-42/",
        )

    def test_company_accepts_public_slug(self) -> None:
        self.assertEqual(
            build_url("company", slug="example-software"),
            "https://www.linkedin.com/company/example-software/posts/",
        )

    def test_profile_rejects_url_and_unsafe_slug(self) -> None:
        for value in (
            "https://www.linkedin.com/in/example",
            "../example",
            "-example",
            "example-",
            "example_member",
            "example?trk=feed",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                build_url("profile", slug=value)

    def test_rejects_unknown_route(self) -> None:
        with self.assertRaises(ValueError):
            build_url("groups")

    def test_cli_rejects_abbreviated_routes_and_options(self) -> None:
        script = Path(__file__).with_name("build_url.py")
        cases = (
            ("sear", "--query", "example"),
            ("search", "--q", "example"),
            ("search", "--query", "example", "--so", "date-posted"),
            ("profile", "--s", "example-member"),
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
