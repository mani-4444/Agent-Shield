"""Stop hook: the agent can't end a turn with failing tests.

Runs tests/unit only until T13; switch to the full suite once AC-1..AC-12 pass
(PLAN.md "Repo setup"). Skips if already re-entered to avoid loops.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

data = json.load(sys.stdin)
if data.get("stop_hook_active"):
    sys.exit(0)

# Fall back to uv's default install dir: editors started before uv was installed keep a stale PATH.
uv = shutil.which("uv") or shutil.which("uv", path=str(Path.home() / ".local" / "bin"))
if uv is None:
    print("Stop gate: `uv` not on PATH, so tests could not run. Fix PATH.", file=sys.stderr)
    sys.exit(2)

r = subprocess.run(
    [uv, "run", "pytest", "tests/unit", "-q", "-x", "--no-header"],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
)
if r.returncode != 0:
    print("Tests are red. Fix them before finishing:\n" + r.stdout[-3000:], file=sys.stderr)
    sys.exit(2)
