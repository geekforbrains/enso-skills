#!/usr/bin/env python3
"""Check the reviewed catalogue and its portable, regular runtime files offline."""

from __future__ import annotations

import json
import re
import stat
import sys
from pathlib import Path, PurePosixPath
from typing import Any

NAME = re.compile(r"enso-[a-z0-9]+(?:-[a-z0-9]+)*")
PART = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*")
FRONTMATTER_FIELDS = {"name", "description", "license", "compatibility"}
BUNDLED_REQUIREMENTS = {"enso-browser"}
# Keep catalogue bounds aligned with Enso's skill_catalog.py installer contract.
BUNDLED_SKILLS = {
    "enso",
    "enso-browser",
    "enso-heartbeat",
    "enso-jobs",
    "enso-security",
    "enso-skills",
    "enso-slack",
    "enso-tables",
    "enso-tasks",
    "enso-update",
    "enso-workspace",
}
MAX_CATALOG_BYTES = 512 * 1024
MAX_FILE_BYTES = 1024 * 1024
MAX_SKILL_BYTES = 8 * 1024 * 1024
MAX_SKILLS = 128
MAX_FILES = 128
YAML_NONSTRINGS = {"true", "false", "yes", "no", "on", "off", "null"}


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _name(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) <= 64
        and NAME.fullmatch(value) is not None
        and value not in BUNDLED_SKILLS
    )


def _safe_path(value: object) -> bool:
    if not isinstance(value, str) or not value or len(value) > 240:
        return False
    return all(PART.fullmatch(part) is not None for part in value.split("/"))


def _regular_file(root: Path, relative: str) -> Path:
    """Reject symlinks and special files before reading a catalogue member."""
    current = root
    for index, part in enumerate(PurePosixPath(relative).parts):
        current = current / part
        mode = current.lstat().st_mode
        final = index == len(PurePosixPath(relative).parts) - 1
        if stat.S_ISLNK(mode):
            raise ValueError(f"symlink is not permitted: {relative}")
        if final and not stat.S_ISREG(mode):
            raise ValueError(f"not a regular file: {relative}")
        if not final and not stat.S_ISDIR(mode):
            raise ValueError(f"not a directory: {relative}")
    return current


def _frontmatter(text: str) -> dict[str, str]:
    """Parse this catalogue's documented single-line YAML scalar subset."""
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("SKILL.md must start with YAML frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as error:
        raise ValueError("SKILL.md frontmatter is not closed") from error
    result: dict[str, str] = {}
    for line in lines[1:end]:
        key, separator, value = line.partition(": ")
        if not separator or key not in FRONTMATTER_FIELDS or key in result:
            raise ValueError("frontmatter requires unique supported single-line fields")
        if (
            not value.strip()
            or value != value.strip()
            or not re.match(r"[A-Za-z]", value)
            or value.lower() in YAML_NONSTRINGS
            or ": " in value
            or " #" in value
            or any(ord(char) < 32 or ord(char) == 127 for char in value)
        ):
            raise ValueError(f"{key} must be an unquoted single-line string")
        result[key] = value
    if not _name(result.get("name")):
        raise ValueError(
            "frontmatter name must be an unbundled enso-* name of at most 64 characters"
        )
    if not 1 <= len(result.get("description", "")) <= 1024:
        raise ValueError("frontmatter description must be 1-1024 characters")
    if len(result.get("compatibility", "")) > 500:
        raise ValueError("frontmatter compatibility must not exceed 500 characters")
    if not any(line.strip() for line in lines[end + 1 :]):
        raise ValueError("SKILL.md requires instruction content after frontmatter")
    return result


def validate(root: Path) -> list[str]:
    """Return independent catalogue problems without making network requests."""
    problems: list[str] = []
    try:
        catalog_path = _regular_file(root, "catalog.json")
        if catalog_path.stat().st_size > MAX_CATALOG_BYTES:
            return ["catalog.json exceeds the 512 KiB size limit"]
        catalog = json.loads(
            catalog_path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object
        )
    except (OSError, UnicodeError, ValueError) as error:
        return [f"catalog.json: {error}"]
    if not isinstance(catalog, dict) or set(catalog) != {"schema_version", "skills"}:
        return ["catalog.json requires only schema_version and skills"]
    if type(catalog["schema_version"]) is not int or catalog["schema_version"] != 1:
        problems.append("schema_version must be 1")
    entries = catalog["skills"]
    if not isinstance(entries, list) or len(entries) > MAX_SKILLS:
        return problems + [f"skills must be an array of at most {MAX_SKILLS} entries"]

    seen: set[str] = set()
    for index, entry in enumerate(entries):
        label = f"skills[{index}]"
        if not isinstance(entry, dict) or not {"name", "description", "files"} <= set(
            entry
        ):
            problems.append(f"{label}: name, description and files are required")
            continue
        if set(entry) - {"name", "description", "files", "requires"}:
            problems.append(f"{label}: unknown catalogue fields")
        name = entry["name"]
        if not _name(name):
            problems.append(f"{label}: invalid skill name")
            continue
        if name in seen:
            problems.append(f"{label}: duplicate skill {name}")
        seen.add(name)
        label = name
        description = entry["description"]
        if (
            not isinstance(description, str)
            or not 1 <= len(description.strip()) <= 1024
        ):
            problems.append(f"{label}: description must be 1-1024 characters")
        requires = entry.get("requires", [])
        if (
            not isinstance(requires, list)
            or any(
                not isinstance(item, str) or item not in BUNDLED_REQUIREMENTS
                for item in requires
            )
            or len(requires) != len(set(requires))
        ):
            problems.append(
                f"{label}: requires must list distinct supported bundled skills"
            )
        files = entry["files"]
        if not isinstance(files, list) or not 1 <= len(files) <= MAX_FILES:
            problems.append(f"{label}: files must list 1-{MAX_FILES} paths")
            continue
        if "SKILL.md" not in files:
            problems.append(f"{label}: files must include SKILL.md")
        seen_files: set[str] = set()
        folded_files = {value.casefold() for value in files if _safe_path(value)}
        safe_files = [value for value in files if _safe_path(value)]
        if len(folded_files) != len(set(safe_files)) or any(
            str(parent).casefold() in folded_files
            for relative in safe_files
            for parent in PurePosixPath(relative).parents
        ):
            problems.append(f"{label}: colliding file paths")
        total_bytes = 0
        for relative in files:
            if not _safe_path(relative):
                problems.append(f"{label}: unsafe relative file path {relative!r}")
                continue
            if relative in seen_files:
                problems.append(f"{label}: duplicate file {relative}")
                continue
            seen_files.add(relative)
            try:
                path = _regular_file(root, f"{name}/{relative}")
                size = path.stat().st_size
                total_bytes += size
                if size > MAX_FILE_BYTES:
                    problems.append(f"{label}/{relative}: exceeds the 1 MiB file limit")
                    continue
                if relative == "SKILL.md":
                    fields = _frontmatter(path.read_text(encoding="utf-8"))
                    if fields["name"] != name:
                        problems.append(f"{label}: folder and frontmatter names differ")
                    if fields["description"] != description:
                        problems.append(
                            f"{label}: catalogue and frontmatter descriptions differ"
                        )
            except (OSError, UnicodeError, ValueError) as error:
                problems.append(f"{label}/{relative}: {error}")
        if total_bytes > MAX_SKILL_BYTES:
            problems.append(f"{label}: exceeds the 8 MiB skill limit")
    return problems


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    problems = validate(root)
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1
    print("Catalogue and skill files are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
