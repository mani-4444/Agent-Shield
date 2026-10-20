"""PostToolUse hook: format and lint-fix only the file just edited.

Formatting only that file (not `.`) keeps the hook from rewriting protected paths such as
tests/acceptance/. Never blocks: lint errors surface in `ruff check` / CI instead.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

data = json.load(sys.stdin)
tool_input = data.get("tool_input") or {}
path = Path(str(tool_input.get("file_path") or ""))
# Fall back to uv's default install dir: editors started before uv was installed keep a stale PATH.
uv = shutil.which("uv") or shutil.which("uv", path=str(Path.home() / ".local" / "bin"))

if uv and path.suffix in (".py", ".pyi") and path.is_file():
    subprocess.run([uv, "run", "ruff", "format", "--quiet", str(path)], check=False)
    subprocess.run([uv, "run", "ruff", "check", "--fix", "--quiet", str(path)], check=False)
sys.exit(0)
