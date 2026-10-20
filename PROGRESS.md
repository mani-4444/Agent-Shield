# Progress: InjectionBench v1   Last updated: 2026-10-20 by T01–T03 session

## Current state
T01 merged (PR #1), T02 merged (PR #2, `a5e84e5`). T03 (`schema.py`, `rng.py` + unit tests) done, uncommitted, awaiting branch + commit approval. `uv run pytest -q`: 54 passed, 1 skipped, 88 xfailed. Next: T04.

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
| F1 | Repo setup, hooks, CI | T01 | done |
| F2 | Acceptance suite + detector fixtures | T02 | done |
| F3 | Schemas, seeded rng | T03 | done (uncommitted) |
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
- T01 repo setup: `792fc21`, merged via PR #1 as `1cecbad` (2026-10-20); CI green.
- T02 acceptance suite: `da17a8f`, merged via PR #2 as `a5e84e5` (2026-10-20); CI green. Written by the agent in a scratch dir and copied into the protected `tests/acceptance/` by the human (agent may not write there). Raw run fails only on missing modules/commands; no collection errors. File list and deviations from PLAN.md: see commit and "Decisions made".

## In progress
- (none)

## Uncommitted changes awaiting approval
T03, proposed branch `feat/t03-schema-rng` from `main` (not created yet):
- `src/injbench/schema.py`: DESIGN §3 models (strict, `extra="forbid"`), ExtractedFacts validators, `record_key`, `LLMResponse`.
- `src/injbench/rng.py`: `make_rng(seed, *keys)`.
- `tests/unit/test_schema.py`, `tests/unit/test_rng.py` (37 tests).
- PROGRESS.md: T02 merged, T03 status.

## Next up
1. Approve branch `feat/t03-schema-rng` + T03 commit; push and PR.
2. Answer open questions 1–4 in SPEC.md Part 1 (they affect T08/T10).
3. T04 (`engine.decide` + `agent/policy.md`); each task deletes its entries from `PENDING_ACCEPTANCE` when its ACs pass.

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
- T02 (2026-10-20), decisions taken by the agent under the human's "take decisions" grant:
  - Interfaces the acceptance suite imports are recorded in DESIGN.md §12 (signatures, CLI flags, file formats).
  - Pending ACs run as strict xfail (`tests/conftest.py`), so `uv run pytest -q` and CI stay green while the oracle is red by design; the implementing task deletes the entry.
  - Production imports sit inside test functions so a missing module fails one test instead of breaking collection.
  - Dataset tests generate their own data in a temp dir via `injbench data` (no dependency on committed `data/v1/`).
  - AC-3 also bans real bank/UPI brand names and any `+91` not followed by ` 0` (AGENTS.md "Never", SPEC Part 4), and self-tests its regexes so it can't pass vacuously.
  - AC-4 also checks twin inheritance (profile, type, gold) and goal/twin fit from DESIGN §5 (G1 on non-APPROVE, G2 on APPROVE).
  - AC-9 fixtures: 6 benign + 3 success/3 non-success per goal; `null` expected = not asserted, used only where a definition is genuinely ambiguous (decision_correct when extra tool calls accompany a matching decision). Canary "last 8 characters" fixtures pass under either reading (raw or normalised tail).
  - AC-10 simulates a kill with KeyboardInterrupt plus a half-written last line; the runner must leave only valid lines.
  - AC-11 checks the spec's same-run-id replay byte-for-byte, plus a fresh run-id served fully from cache (outcomes equal; not summary bytes, since wall-clock engine latency differs), plus non-zero exit on cache miss.
  - AC-12 fixes percentiles to numpy's linear method, `tokens_per_doc` as mean tokens per trial (blocked trials count as 0), and classifier FPR per benign doc.
  - AC-15's real >=95% gate skips until T18 writes `results/v1-main/label_check.md`.
- T03 (2026-10-20):
  - Every model is strict and rejects unknown fields (DESIGN only required it for ExtractedFacts); catches typos in generated data and fixtures early.
  - ExtractedFacts' "date within ±400 days of doc date" check runs only when the caller passes `context={"doc_date": ...}` (documents carry no date field of their own).
  - Invariants added in the schema: RunRecord `key == config|doc_id|trial`; Profile canary starts `CANARY-`. No twin_id/attack pairing invariant, because acceptance tests build poisoned docs without twins.
  - `LLMRequest` deferred to T08 (its message/tool shape depends on the adapter); `LLMResponse` defined now, as the suite constructs it.
  - `make_rng` hashes `json.dumps([seed, *keys])` with SHA-256 into PCG64: no `hash()`, no global state, NFC-normalised string keys, int and str keys distinct.
  - PR #3 CI failed on I001 in two protected acceptance files: ruff classifies `injbench.<mod>` as first-party only once `<mod>` exists, so adding `schema.py` changed the expected import order; local runs passed on a stale ruff cache. Fix in pyproject: `known-first-party = ["injbench"]` and I001 ignored for `tests/acceptance/**` (frozen; also keeps `ruff check --fix .` from rewriting them). Lesson: run `ruff check . --no-cache` before proposing a commit.
