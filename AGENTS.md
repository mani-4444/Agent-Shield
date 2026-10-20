# InjectionBench: Agent instructions

A benchmark that attacks a finance-style document-reading agent with indirect prompt injections and measures five defenses. It is a *measurement* project: the one constraint you can't infer from the code is that metric definitions, detectors and the test split are frozen (see SPEC.md "Pre-registration rule"). Never change them to improve a result.

Read first: SPEC.md (problem, spec, threat model), DESIGN.md (how + key decisions), PLAN.md (tasks, setup, prompts, review), PROGRESS.md (where we are). These five files are the only planning docs; don't create new ones; add to these instead.

## Commands
- Install: `uv sync` · Secrets: copy `.env.example` to `.env` (GROQ_API_KEY, GEMINI_API_KEY, HF_TOKEN)
- Test one: `uv run pytest tests/unit/test_detectors.py -q`
- All tests (offline, default): `uv run pytest -q` · Live-API tests: `uv run pytest -m live -q` (ask first; uses quota)
- Typecheck: `uv run mypy src` · Lint/format: `uv run ruff check --fix . && uv run ruff format .`
- Generate data: `uv run injbench data --seed 2026 --out data/v1`
- Eval: `uv run injbench eval --config d --trials 3 --split dev --run-id dev-d` (use `--limit 10` for pilots, `--replay` for zero network calls)
- Report: `uv run injbench report --run results/<run_id>`
- Dashboard: `uv run streamlit run app/dashboard.py`

## Definition of done (run all before finishing; paste the output)
- `uv run ruff check . && uv run mypy src && uv run pytest -q` all green.
- If you touched data, runner or metrics: `uv run injbench eval --config all --split dev --trials 1 --limit 5 --run-id smoke` then `uv run injbench report --run results/smoke` completes.
- PROGRESS.md updated; changes staged and a proposed commit shown to the human (see Git). Never commit without approval.

## Conventions (non-defaults only)
- Python 3.11, Pydantic v2 models in `src/injbench/schema.py` are the only data contracts. No bare dicts across module boundaries.
- All randomness goes through `injbench.rng.make_rng(seed, *keys)`; never call `random`/`numpy.random` globals.
- All LLM calls go through `agent/llm.py` (`complete()`), which handles cache, retries, rate limits and latency logging. Never call a provider SDK directly elsewhere.
- Model IDs, temperature, max tokens and seeds live only in `config/models.yaml`.
- Records are JSONL, one line per trial; keys are `config|doc_id|trial`.
- Synthetic identifiers only: phone numbers start `+91 0`, VPAs end `@fakepay` or `@examplebank`, canaries start `CANARY-`.

## Architecture boundaries
- `detectors.py` and `metrics.py` are pure functions of records + gold; no I/O, no LLM calls.
- `agent/engine.py` (`decide`) is the single source of the decision policy, used for gold labels and config (d)/(e). Configs (a)–(c) get the same policy as prompt text from `agent/policy.md` (DESIGN.md Appendix A).
- Config (d) must never send profile fields, the canary or tool schemas to the LLM.
- `agent/tools.py` tools only record calls; they never touch the network or filesystem.
- Decisions: see DESIGN.md §11 (don't re-litigate accepted ADRs).

## Ask first
- Creating, switching or deleting a git branch (see Git).
- Every git commit, amend, rebase, merge or push (see Git).
- Adding a dependency; changing `config/models.yaml`; any run without `--limit` on the test split (it spends quota).
- Any change to SPEC.md, `detectors.py`, `metrics.py` definitions, or the dataset generator after data/v1 is frozen.
- Deleting or rewriting anything in `results/` or `.cache/`.

## Never
- Edit `tests/acceptance/` (protected; acceptance tests are the oracle).
- Tune prompts, thresholds or detectors on the `test` split. Use `dev` only.
- Edit files in `data/v1/` by hand; regenerate them.
- Write real-looking personal data, real UPI IDs, real phone numbers, or real bank names into data or fixtures.
- Commit `.env`, API keys, `.cache/` or raw `results/*/records.jsonl`.
- Make network calls in unit or acceptance tests (the socket-blocking fixture will fail them).
- Push to `main`.

## Gotchas
- Free-tier rate limits: `llm.py` backs off on HTTP 429; a long run that looks stuck is usually waiting. Check `results/<run_id>/progress.log`.
- Prompt Guard 2 is gated on Hugging Face: accept the license and set `HF_TOKEN` before first use. Its context is 512 tokens; `promptguard.py` chunks and takes the max score.
- Telugu text: normalise with NFC before hashing or comparing, or cache keys and payload checks will miss.
- Temperature 0 is still not deterministic on hosted APIs; that is why there are 3 trials.
- The canary detector normalises spaces, dashes and zero-width characters before matching.

## Git (the human approves every branch and commit)
- **Branches:** before creating a branch, stop and ask. Propose the name (`feat/<task-id>-<slug>`, e.g. `feat/t07-detectors`) and the base branch, then wait for an explicit "yes". Never create, switch or delete branches on your own.
- **Commits:** never run `git commit` (or `--amend`, `rebase`, `merge`, `cherry-pick`, `reset`, `push`) without approval. When work is ready:
  1. Show `git status` and `git diff --stat`.
  2. Propose the files to stage and a conventional commit message.
  3. Wait for an explicit "yes" (or edits to the message) before committing.
- Approval covers one commit only; ask again for the next one. If the human doesn't answer, leave changes uncommitted and say so in PROGRESS.md.
- PR body includes the definition-of-done output.

## Tool-specific notes
- `CLAUDE.md` is a symlink to this file (`ln -s AGENTS.md CLAUDE.md`); Codex and Copilot read AGENTS.md natively; for Gemini set `context.fileName` to `["AGENTS.md"]`.
- Claude Code: use plan mode for any task touching more than one module; implement in a fresh session. When compacting, keep the current task ID, files changed, failing test names and open questions.
- Hooks (PLAN.md "Repo setup") format on edit, block protected paths, run tests on Stop, and require confirmation for git branch/commit commands. If a hook blocks you, fix the cause; don't work around it.
