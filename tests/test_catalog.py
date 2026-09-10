"""Exercise catalogue trust boundaries with temporary fictional skills."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from validate import validate  # noqa: E402


class CatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.skill = self.root / "enso-example"
        self.skill.mkdir()
        self.skill_text = (
            "---\nname: enso-example\ndescription: Example skill.\nlicense: MIT\n"
            "---\n\nUse fictional examples.\n"
        )
        (self.skill / "SKILL.md").write_text(self.skill_text, encoding="utf-8")
        self.entry = {
            "name": "enso-example",
            "description": "Example skill.",
            "files": ["SKILL.md"],
            "requires": ["enso-browser"],
        }

    def check(self, entries: list | None = None) -> list[str]:
        catalog = {
            "schema_version": 1,
            "skills": entries if entries is not None else [self.entry],
        }
        (self.root / "catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
        return validate(self.root)

    def test_valid_skill_and_optional_dependencies(self) -> None:
        self.assertEqual(self.check(), [])
        del self.entry["requires"]
        self.assertEqual(self.check(), [])

    def test_rejects_unsafe_paths_before_reading(self) -> None:
        for path in (
            "../outside",
            "/etc/passwd",
            "scripts/../SKILL.md",
            "a//b",
            "./SKILL.md",
            ".env",
            "a\\b",
            "a\nb",
            "file name.md",
            "file:name.md",
            "café.md",
            "a" * 241,
        ):
            with self.subTest(path=path):
                self.entry["files"] = ["SKILL.md", path]
                self.assertTrue(
                    any("unsafe relative file path" in item for item in self.check())
                )

    def test_rejects_non_enso_and_bundled_names(self) -> None:
        for name in ("example", "enso", "enso-browser", "enso-skills", "enso-security"):
            with self.subTest(name=name):
                self.entry["name"] = name
                self.assertTrue(
                    any("invalid skill name" in item for item in self.check())
                )

    def test_rejects_casefold_and_file_directory_collisions(self) -> None:
        for files in (["SKILL.md", "skill.md"], ["SKILL.md", "docs", "docs/page.md"]):
            with self.subTest(files=files):
                self.entry["files"] = files
                self.assertTrue(
                    any("colliding file paths" in item for item in self.check())
                )

    def test_rejects_catalog_and_file_count_overflow(self) -> None:
        self.assertTrue(
            any("at most 128" in item for item in self.check([self.entry] * 129))
        )
        self.entry["files"] = ["SKILL.md"] + [f"file-{i}.md" for i in range(128)]
        self.assertTrue(any("1-128 paths" in item for item in self.check()))

    def test_rejects_oversized_catalog_file_and_skill(self) -> None:
        (self.root / "catalog.json").write_bytes(b" " * (512 * 1024 + 1))
        self.assertTrue(any("512 KiB" in item for item in validate(self.root)))
        (self.skill / "large.md").write_bytes(b"a" * (1024 * 1024 + 1))
        self.entry["files"].append("large.md")
        self.assertTrue(any("1 MiB" in item for item in self.check()))
        self.entry["files"] = ["SKILL.md"]
        for index in range(8):
            name = f"part-{index}.md"
            (self.skill / name).write_bytes(b"a" * (1024 * 1024))
            self.entry["files"].append(name)
        self.assertTrue(any("8 MiB" in item for item in self.check()))

    def test_rejects_symlink_files_and_directories(self) -> None:
        (self.skill / "linked.md").symlink_to("SKILL.md")
        (self.skill / "linked-dir").symlink_to(self.skill, target_is_directory=True)
        for relative in ("linked.md", "linked-dir/SKILL.md"):
            with self.subTest(relative=relative):
                self.entry["files"] = ["SKILL.md", relative]
                self.assertTrue(
                    any("symlink is not permitted" in item for item in self.check())
                )

    @unittest.skipUnless(hasattr(os, "mkfifo"), "requires named pipes")
    def test_rejects_special_file_without_opening_it(self) -> None:
        os.mkfifo(self.skill / "pipe")
        self.entry["files"].append("pipe")
        self.assertTrue(any("not a regular file" in item for item in self.check()))

    def test_reports_missing_file_and_missing_entrypoint(self) -> None:
        self.entry["files"] = ["missing.md"]
        problems = self.check()
        self.assertTrue(any("must include SKILL.md" in item for item in problems))
        self.assertTrue(any("missing.md" in item for item in problems))

    def test_rejects_duplicates(self) -> None:
        self.entry["files"].append("SKILL.md")
        problems = self.check([self.entry, self.entry])
        self.assertTrue(any("duplicate skill" in item for item in problems))
        self.assertTrue(any("duplicate file" in item for item in problems))

    def test_rejects_unknown_or_malformed_dependencies(self) -> None:
        for requires in (
            ["third-party"],
            ["enso-browser", "enso-browser"],
            [{}],
            "enso-browser",
        ):
            with self.subTest(requires=requires):
                self.entry["requires"] = requires
                self.assertTrue(
                    any("requires must list" in item for item in self.check())
                )

    def test_rejects_name_and_description_mismatch(self) -> None:
        changed = self.skill_text.replace("enso-example", "enso-other").replace(
            "Example skill.", "Other skill."
        )
        (self.skill / "SKILL.md").write_text(changed, encoding="utf-8")
        problems = self.check()
        self.assertTrue(any("names differ" in item for item in problems))
        self.assertTrue(any("descriptions differ" in item for item in problems))

    def test_rejects_malformed_frontmatter(self) -> None:
        for text in (
            "no frontmatter",
            "---\nname: enso-example",
            self.skill_text.replace("name: enso-example", "name: Enso-Example"),
            self.skill_text.replace(
                "description: Example skill.", "description: Example: skill"
            ),
            self.skill_text.replace(
                "description: Example skill.", "description: |\n  Example skill."
            ),
            self.skill_text.replace("license: MIT", "license: MIT\nlicense: MIT"),
            self.skill_text.replace("license: MIT", "license: true"),
            self.skill_text.replace("license: MIT", "compatibility: 123"),
            self.skill_text.replace("license: MIT", "license: null"),
            self.skill_text.replace(
                "description: Example skill.", "description: " + "x" * 1025
            ),
        ):
            with self.subTest(text=text[:70]):
                (self.skill / "SKILL.md").write_text(text, encoding="utf-8")
                self.assertTrue(self.check())

    def test_rejects_duplicate_json_keys(self) -> None:
        (self.root / "catalog.json").write_text(
            '{"schema_version": 1, "skills": [], "skills": []}', encoding="utf-8"
        )
        self.assertTrue(
            any("duplicate JSON key" in item for item in validate(self.root))
        )

    def test_independent_entries_report_independent_problems(self) -> None:
        problems = self.check(
            [{"name": "../outside", "description": "Bad.", "files": []}, {}]
        )
        self.assertEqual(len(problems), 2)


if __name__ == "__main__":
    unittest.main()
