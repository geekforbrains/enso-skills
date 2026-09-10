# Enso Skills

Official, reviewed optional skills for [Enso](https://github.com/geekforbrains/enso).
Each skill adds a focused workflow; install only the ones you need.

```sh
enso skill list --available
enso skill install enso-linkedin
enso skill list
```

Enso's installer accepts skills only from this repository and pins each install
to a Git commit. Review is a maintained trust boundary, not a sandbox: skills can
run code and use the accounts and tools you give Enso access to.

| Skill | What it does |
| --- | --- |
| [enso-linkedin](enso-linkedin/SKILL.md) | Read LinkedIn feeds, search and profiles, and Like an authorized post. |
| [enso-x](enso-x/SKILL.md) | Read X timelines, search and threads, and Like an authorized post. |

Both use `enso-browser`, which ships with Enso. The bundled `enso-skills` skill
explains manual authoring and installation locations; those core skills live in
the Enso repository. Skills here do not include accounts, login sessions or
personal configuration.

## Contributing

Discuss a new skill or substantial change in an issue first, then send a small
pull request. Follow the [Agent Skills specification](https://agentskills.io/specification):
the folder and frontmatter name must match, and `SKILL.md` should contain concise
instructions with detailed workflows in linked references when useful.

Keep skills useful across accounts and machines. Never include secrets, login
sessions, private data, or personal workflow assumptions. Browser skills delegate
profile selection and login to `enso-browser`; the user controls account identity
and external actions. Tests use fictional data and run offline.

`catalog.json` is the explicit installation allowlist. Every new skill, listed
file and bundled dependency receives review. Paths are relative to the skill's
folder; list only files needed at runtime. Tests stay in this repository.
The catalogue currently permits `enso-browser` as a bundled dependency, with no
automatic third-party dependency installation.

Run the checks before opening a pull request:

```sh
python3 scripts/validate.py
python3 -m unittest discover -s tests
python3 -m unittest discover -s enso-linkedin/scripts -p 'test_*.py'
python3 -m unittest discover -s enso-x/scripts -p 'test_*.py'
```

The validator enforces the installer's name, path, size and file-type limits plus
this repository's small frontmatter subset: unquoted, single-line `name`,
`description`, `license`, and `compatibility` strings beginning with a letter.
YAML booleans such as `true` or `yes` are not strings. Enso's installer owns full
specification validation. Offline checks cannot prove
that a site's current interface still matches a skill; report browser changes
with a minimal, redacted example and verify controls before any action.

Changes use Conventional Commits. Reviewed changes land on `main`; the commit is
the catalogue revision, so there are no separate skill versions or release tags.
Enso's application releases follow its own release process.

MIT licensed; see [LICENSE](LICENSE).
