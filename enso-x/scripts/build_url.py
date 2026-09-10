#!/usr/bin/env python3
"""Build and validate allowlisted X URLs."""

from __future__ import annotations

import argparse
import re
from urllib.parse import quote, urlencode, urlsplit

BASE_URL = "https://x.com"
HANDLE = re.compile(r"[A-Za-z0-9_]{1,15}")
STATUS_PATH = re.compile(
    r"/(?P<handle>[A-Za-z0-9_]{1,15})/status/(?P<status_id>[0-9]{1,20})"
)
MAX_STATUS_ID = (1 << 64) - 1
SEARCH_TABS = {"top": "top", "latest": "live"}
RESERVED_HANDLES = {
    "about",
    "account",
    "compose",
    "explore",
    "home",
    "i",
    "intent",
    "jobs",
    "login",
    "logout",
    "messages",
    "notifications",
    "privacy",
    "search",
    "settings",
    "share",
    "signup",
    "tos",
}


def validate_handle(value: str) -> str:
    """Return a canonical X handle without its optional leading at-sign."""
    candidate = value[1:] if value.startswith("@") else value
    if not HANDLE.fullmatch(candidate):
        raise ValueError("handle must be 1-15 ASCII letters, numbers, or underscores")
    candidate = candidate.lower()
    if candidate in RESERVED_HANDLES:
        raise ValueError("handle collides with a reserved X route")
    return candidate


def validate_status_id(value: str) -> str:
    """Validate a positive unsigned 64-bit decimal X status ID."""
    if not re.fullmatch(r"[1-9][0-9]{0,19}", value):
        raise ValueError("status ID must be a positive decimal integer")
    if int(value) > MAX_STATUS_ID:
        raise ValueError("status ID exceeds the unsigned 64-bit range")
    return value


def validate_query(value: str) -> str:
    """Validate an X search expression while preserving its query grammar."""
    query = value.strip()
    if not query:
        raise ValueError("search query must not be empty")
    if len(query) > 512:
        raise ValueError("search query must not exceed 512 characters")
    for character in query:
        codepoint = ord(character)
        if codepoint < 32 or 127 <= codepoint <= 159:
            raise ValueError("search query must not contain control characters")
        if character.isspace() and character != " ":
            raise ValueError("search query may use ordinary spaces only")
        if 0xD800 <= codepoint <= 0xDFFF:
            raise ValueError("search query must not contain Unicode surrogates")
    return query


def build_url(
    route: str,
    *,
    handle: str | None = None,
    status_id: str | None = None,
    query: str | None = None,
    tab: str | None = None,
) -> str:
    """Build one allowlisted X route from validated components."""
    if route == "home":
        return f"{BASE_URL}/home"
    if route == "search":
        if query is None:
            raise ValueError("search route requires a query")
        if tab not in SEARCH_TABS:
            raise ValueError("search route requires tab top or latest")
        params = {
            "q": validate_query(query),
            "f": SEARCH_TABS[tab],
        }
        return f"{BASE_URL}/search?{urlencode(params, quote_via=quote, safe='')}"
    if route == "profile":
        if handle is None:
            raise ValueError("profile route requires a handle")
        return f"{BASE_URL}/{validate_handle(handle)}"
    if route == "status":
        if handle is None or status_id is None:
            raise ValueError("status route requires a handle and status ID")
        return (
            f"{BASE_URL}/{validate_handle(handle)}/status/"
            f"{validate_status_id(status_id)}"
        )
    raise ValueError(f"unsupported route: {route}")


def validate_status_url(value: str) -> str:
    """Validate a clean x.com status permalink and return its canonical form."""
    if value != value.strip():
        raise ValueError("status URL must not contain surrounding whitespace")
    if any(ord(character) < 33 or 127 <= ord(character) <= 159 for character in value):
        raise ValueError("status URL must not contain spaces or control characters")
    if "?" in value or "#" in value:
        raise ValueError("status URL must not contain a query or fragment delimiter")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as error:
        raise ValueError("status URL is malformed") from error
    if parsed.scheme != "https":
        raise ValueError("status URL must use https")
    if parsed.hostname != "x.com" or parsed.netloc.lower() != "x.com":
        raise ValueError("status URL host must be exactly x.com")
    if parsed.username is not None or parsed.password is not None or port is not None:
        raise ValueError("status URL must not contain credentials or a port")
    if parsed.query or parsed.fragment:
        raise ValueError("status URL must not contain a query or fragment")
    match = STATUS_PATH.fullmatch(parsed.path)
    if match is None:
        raise ValueError("status URL path must be /<handle>/status/<status-id>")
    return build_url(
        "status",
        handle=match.group("handle"),
        status_id=match.group("status_id"),
    )


def parser() -> argparse.ArgumentParser:
    """Create the strict command-line parser."""
    result = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    subparsers = result.add_subparsers(dest="route", required=True)
    subparsers.add_parser("home", allow_abbrev=False)
    search = subparsers.add_parser("search", allow_abbrev=False)
    search.add_argument("--query", required=True)
    search.add_argument("--tab", choices=tuple(SEARCH_TABS), required=True)
    profile = subparsers.add_parser("profile", allow_abbrev=False)
    profile.add_argument("--handle", required=True)
    status = subparsers.add_parser("status", allow_abbrev=False)
    status.add_argument("--handle", required=True)
    status.add_argument("--status-id", required=True)
    status_url = subparsers.add_parser("validate-status-url", allow_abbrev=False)
    status_url.add_argument("--url", required=True)
    return result


def main() -> int:
    """Build or validate a URL from command-line arguments."""
    argument_parser = parser()
    args = argument_parser.parse_args()
    try:
        if args.route == "validate-status-url":
            url = validate_status_url(args.url)
        else:
            url = build_url(
                args.route,
                handle=getattr(args, "handle", None),
                status_id=getattr(args, "status_id", None),
                query=getattr(args, "query", None),
                tab=getattr(args, "tab", None),
            )
        print(url)
    except ValueError as error:
        argument_parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
