# Progress: InjectionBench v1   Last updated: 2026-10-20 by T01 session

## Current state
T01 done (uncommitted, awaiting branch + commit approval): uv project, placeholder `injbench` CLI, ruff/mypy/pytest config, offline socket blocking, hooks, CI. Next: T02.

## Gates
| Gate | Stage | Where | Status |
|---|---|---|---|
| Problem statement and success metric | 1 | SPEC.md Part 1 | ☐ sign off |
| Spec, acceptance criteria and threat model approved (freezes metrics/detectors) | 3 | SPEC.md Parts 2–3 | ☐ sign off |
| ADR-3 model choice confirmed | 4 | DESIGN.md §11, after T08 | ☐ |
| Plan approved | 5 | PLAN.md | ☐ sign off |
| Data, prompts and τ frozen after pilot | 7 | T14 | ☐ |
| Human review and `v1.0` tag | 9 | T21 | ☐ |

## Feature list
| ID | Feature | Tasks | Status |
|---|---|---|---|
| F1 | Repo setup, hooks, CI | T01 | done (uncommitted) |
| F2 | Acceptance suite + detector fixtures | T02 | todo |
| F3 | Schemas, seeded rng | T03 | todo |
| F4 | Decision engine + policy text | T04 | todo |
| F5 | Benign generator (en/te/te-en) | T05 | todo |
| F6 | Attack injector (6 families × 3 goals) | T06 | todo |
| F7 | Detectors | T07 | todo |
| F8 | Mock tools + cached LLM adapter | T08 | todo |
| F9 | Configs a–e (+ optional d′) | T09–T11 | todo |
| F10 | Runner (resume, replay) | T12 | todo |
| F11 | Metrics with cluster bootstrap | T13 | todo |
| F12 | Pilot + freeze | T14 | todo |
| F13 | Full test run | T15 | todo |
| F14 | AgentDojo subset (stretch) | T16 | todo |
| F15 | Report, label check, dashboard | T17–T19 | todo |
| F16 | README, demo, review, release | T20–T21 | todo |

## Done (with commit SHAs, after your approval)
- (none yet)

## In progress
- (none)

## Uncommitted changes awaiting approval
T01, proposed branch `feat/t01-repo-setup` from `main` (not created yet):
- Renamed `DESIGN (2).md` → `DESIGN.md`, `PLAN (1).md` → `PLAN.md` (names the docs reference).
- `pyproject.toml` (Python 3.11, uv_build, `injbench` script, deps as approved, CPU torch index on Linux, ruff/mypy/pytest config), `.python-version`, `uv.lock`.
- `src/injbench/{__init__.py,cli.py,py.typed}`: placeholder Typer CLI (help only).
- `tests/conftest.py` (`live` tests get sockets back), `tests/unit/test_cli.py`, `tests/unit/test_offline.py`.
- `.gitignore`, `.env.example` (verbatim from PLAN.md), `config/models.yaml` (TODO placeholders).
- `CLAUDE.md`: `@AGENTS.md` import (fallback; symlink needs admin/Developer Mode on this machine).
- `.claude/settings.json`, `.claude/hooks/{protect_paths,stop_gate,format_edited}.py`.
- `.github/workflows/ci.yml`: uv sync --locked, ruff check, mypy src, pytest (offline).
- This file.

## Next up
1. Approve branch + commit for T01.
2. Answer open questions 1–4 in SPEC.md Part 1 (they affect T08/T10).
3. T02 (acceptance tests first; extend the existing `tests/conftest.py`, don't recreate it) → T03.

## Decisions made
- Size Large, trimmed: five planning docs only; no separate ADR, threat-model or prompt files.
- Prompt Guard 2 86M run locally; threshold calibrated on dev only (DESIGN.md ADR-3).
- Temperature 0 + 3 trials; report mean and worst-of-3 ASR.
- No FastAPI service in v1; Streamlit calls the library directly.
- Every git branch and commit needs explicit human approval (AGENTS.md "Git").
- T01 (2026-10-20), deviations from PLAN.md "Repo setup", approved by human:
  - Network blocking uses pytest-socket `--allow-hosts=127.0.0.1,::1` instead of `--disable-socket`: on Windows asyncio's self-pipe is a loopback TCP socketpair, which `--disable-socket` breaks (would hit AC-14 Streamlit AppTest). All non-loopback connects still raise.
  - `protect_paths.py` normalises Windows backslashes/case and matches `.env`/`uv.lock` by file name (PLAN's substring version never matched Windows paths and blocked `.env.example`).
  - PostToolUse hook formats only the edited file (`format_edited.py`), not `.`, so it can't rewrite `tests/acceptance/`.
  - Git `ask` rules also cover the PowerShell tool and all `git checkout` (branch switching).
  - Stop gate runs `tests/unit` only until T13 (PLAN.md note); a CLI smoke test exists so it isn't "no tests collected" (exit 5).
  - `ruff format` excludes `*.md`: ruff 0.17 formats Python code blocks in Markdown and would rewrite DESIGN/PLAN snippets.
  - torch resolved from the PyTorch CPU index on Linux (CI) to avoid ~2.5 GB CUDA wheels.
  - Deferred from PLAN checklist: gitleaks + pip-audit in CI, CODEOWNERS, branch protection on `main` (GitHub setting, human), sandbox config.

## Known issues / blockers
- Prompt Guard 2 needs Hugging Face license acceptance + `HF_TOKEN` before T10.
- `uv` was installed to `%USERPROFILE%\.local\bin` during T01 (user PATH updated); restart VS Code so its processes pick it up. Hooks also fall back to that dir, since the Stop gate initially failed on the stale PATH.
- Hooks are live in-session. In T01 the protect-paths script was verified by direct invocation; a live write to `tests/acceptance/` was stopped by the permission deny rule first.
- `CLAUDE.md` is an `@AGENTS.md` import, not a symlink. To switch: enable Windows Developer Mode, `git config core.symlinks true`, recreate as a symlink.
- mypy will need `types-PyYAML` / `pandas-stubs` once code imports them (new dev deps: ask at that task).

## How to resume
```bash
git pull && uv sync
cat PROGRESS.md && git log --oneline -15
uv run pytest -q                       # smoke: what's green/red
# then do the top unfinished task in PLAN.md only; update this file;
# ask before creating a branch; propose the commit and wait for approval
```
