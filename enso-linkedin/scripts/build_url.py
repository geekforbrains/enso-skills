#!/usr/bin/env python3
"""Build allowlisted LinkedIn URLs without interpolating raw values."""

from __future__ import annotations

import argparse
import re
from urllib.parse import urlencode

BASE_URL = "https://www.linkedin.com"
PROFILE_SLUG = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,98}[A-Za-z0-9])?")
SORT_VALUES = {"relevance": "relevance", "date-posted": "date_posted"}
DATE_VALUES = {
    "past-24h": "past-24h",
    "past-week": "past-week",
    "past-month": "past-month",
}


def _query(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("search query must not be empty")
    if len(value) > 512:
        raise ValueError("search query must not exceed 512 characters")
    if any(ord(char) < 32 or 127 <= ord(char) <= 159 for char in value):
        raise ValueError("search query must not contain control characters")
    if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        raise ValueError("search query must not contain Unicode surrogates")
    return value


def _slug(value: str) -> str:
    if not PROFILE_SLUG.fullmatch(value):
        raise ValueError(
            "profile slug must contain only letters, numbers, and interior hyphens"
        )
    return value


def build_url(
    route: str,
    *,
    query: str | None = None,
    slug: str | None = None,
    sort: str | None = None,
    date_posted: str | None = None,
) -> str:
    if route == "feed":
        return f"{BASE_URL}/feed/"
    if route == "me":
        return f"{BASE_URL}/in/me/"
    if route == "search":
        if query is None:
            raise ValueError("search route requires a query")
        params = {"keywords": _query(query)}
        if sort is not None:
            if sort not in SORT_VALUES:
                raise ValueError(f"unsupported search sort: {sort}")
            params["sortBy"] = f'"{SORT_VALUES[sort]}"'
        if date_posted is not None:
            if date_posted not in DATE_VALUES:
                raise ValueError(f"unsupported search date: {date_posted}")
            params["datePosted"] = f'"{DATE_VALUES[date_posted]}"'
        return f"{BASE_URL}/search/results/content/?{urlencode(params)}"
    if route == "profile":
        if slug is None:
            raise ValueError("profile route requires a slug")
        return f"{BASE_URL}/in/{_slug(slug)}/"
    if route == "company":
        if slug is None:
            raise ValueError("company route requires a slug")
        return f"{BASE_URL}/company/{_slug(slug)}/posts/"
    raise ValueError(f"unsupported route: {route}")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    subparsers = result.add_subparsers(dest="route", required=True)
    subparsers.add_parser("feed", allow_abbrev=False)
    subparsers.add_parser("me", allow_abbrev=False)
    search = subparsers.add_parser("search", allow_abbrev=False)
    search.add_argument("--query", required=True)
    search.add_argument("--sort", choices=tuple(SORT_VALUES))
    search.add_argument("--date-posted", choices=tuple(DATE_VALUES))
    profile = subparsers.add_parser("profile", allow_abbrev=False)
    profile.add_argument("--slug", required=True)
    company = subparsers.add_parser("company", allow_abbrev=False)
    company.add_argument("--slug", required=True)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        print(
            build_url(
                args.route,
                query=getattr(args, "query", None),
                slug=getattr(args, "slug", None),
                sort=getattr(args, "sort", None),
                date_posted=getattr(args, "date_posted", None),
            )
        )
    except ValueError as error:
        parser().error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
