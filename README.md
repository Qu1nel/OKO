# OKO

A local-first flashcard app for short study sessions, with spaced repetition and forgetting-curve insights.
Create and reopen text flashcards in the local collection. The dashboard and editor use Django templates and locally built CSS and TypeScript.

Application code lives in [`src/oko/`](src/oko/), with frontend assets in [`frontend/`](frontend/).
The public tools in [`scripts/`](scripts/) handle setup, checks, pre-commit, and releases, locally and in CI.

Development requires Git, GnuPG (including `gpgconf`), the Python version in `.python-version`, and uv 0.13.7.
Run these commands from the project root in a terminal, including the one in free PyCharm. Pro is not required:

```console
uv sync --locked
uv run --locked python scripts/setup_node.py
uv run --locked python scripts/node.py npm ci --no-audit --no-fund
uv run --locked python scripts/check.py
uv run --locked pre-commit install
```

Node and npm are installed in `.tools` without changing the system installation. The bootstrap supports
Windows x64 and Linux x64, with archive checksums pinned in the setup script.

`scripts/check.py --only python` and `--only frontend` run groups of checks. Individual checks are
`python-lint`, `python-format`, `python-types`, `python-tests`, `frontend-types`, `frontend-format`,
`frontend-build`. Pre-commit checks only staged Python/TS/CSS files without modifying them.
The hook uses the installed uv and existing `.venv`; activation and Python on PATH are not required.
It does not install packages, create an environment, or access the network.

Place tests in the directory for the area they exercise. Use [`tests/app/`](tests/app/) for the runtime,
FSRS, and web application, and [`tests/tooling/`](tests/tooling/) for development commands, hooks, and releases.
Include `__init__.py` in each test subdirectory so Django's test runner can find its `test_*.py` files.

On Windows, create the local data directory once from PowerShell:

```powershell
New-Item -ItemType Directory -Force -Path (Join-Path $env:LOCALAPPDATA 'OKO')
```

On Linux, create `${XDG_DATA_HOME:-$HOME/.local/share}/oko`. For a separate collection, set `OKO_DB_PATH` to an absolute file path and create its parent directory before migrating. The app and migrations use the same path. Automated tests use an in-memory SQLite database.

Run the app from this source checkout after installing the dependencies above:

```console
uv run --locked python scripts/node.py npm run build
uv run --locked python manage.py migrate
uv run --locked python manage.py runserver 127.0.0.1:8000
```

Open `http://127.0.0.1:8000/` and follow the link to the dashboard.
Open Cards, create a text flashcard, then open it from the collection. Statistics and Settings are placeholders.
The light or dark theme follows the browser across pages and restarts. The cookie expires after 90 days without a visit.
The default SQLite file is `oko.sqlite3` in the local data directory above. Keep that file outside version control.
This uses Django's development server and development-only settings. Packaged wheel deployment is not supported yet.

Vite builds local assets and `dist/.vite/manifest.json`; Django reads the entry's JS/CSS paths from it.
Only `dist/assets` is served under `/static/assets/`. Rebuild after frontend changes; no Vite dev server is needed.
If the build is missing or invalid, Django reports a rebuild instruction in development mode.
With `DEBUG=False`, Django shows custom 404 and 500 pages. To preview them with styles locally, run `manage.py runserver 127.0.0.1:8000 --insecure`. The error pages remain readable if the build is unavailable.
After installation and a build, this page requires no external network resources.
`python-tests` builds the assets before its HTTP tests and stops if that build fails; Node/npm dependencies
are therefore required for `--only python` and `--only python-tests` too. CI prepares them in the Python test job.
To format frontend files: `uv run --locked python scripts/node.py npm run format`.

CI defines separate checks for pull requests to `main` and manual runs. Protect `main` before relying on
this setup: require pull requests, all seven checks, and an up-to-date branch before merging.
A normal merge into `main` does not repeat the full CI run.

Before a release, align versions in `pyproject.toml`, `uv.lock`, `package.json`, and `package-lock.json`,
including `packages[""].version` in the npm lock file. Update the lock files with `uv lock` and
`uv run --locked python scripts/node.py npm install --package-lock-only --ignore-scripts --no-audit --no-fund`.
Move brief Unreleased notes into a dated `## [X.Y.Z] - YYYY-MM-DD` section and run
`uv run --locked python scripts/release.py --tag vX.Y.Z`. The signed tag must point to a verified commit
on `main`. The tag workflow validates versions and notes, runs all checks, then creates a GitHub Release.
`--require-tag` also runs `git verify-tag`; the signing public key must be available locally.
Before using the release workflow, set repository variable `OKO_RELEASE_PUBLIC_KEY` to the armored OpenPGP
public key and register it with the signing GitHub account. CI imports it into an isolated keyring;
publication also requires GitHub to report the tag signature as verified. Private keys stay local.
These workflows are prepared configuration until they have run on GitHub and branch protection is verified.

Licensed under [MIT](LICENSE).
