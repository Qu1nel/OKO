# OKO

A local-first flashcard app for short study sessions, with spaced repetition and forgetting-curve insights.
The project is being set up; there is no user interface yet.

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

Vite builds local assets and `dist/.vite/manifest.json` for future Django templates.
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
