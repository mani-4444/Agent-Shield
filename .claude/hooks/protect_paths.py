"""PreToolUse hook: block edits to protected paths (AGENTS.md "Never").

Exit code 2 blocks the tool call and sends stderr back to the agent.
"""

import json
import sys

PROTECTED_DIRS = ("tests/acceptance/", "data/v1/")
PROTECTED_NAMES = (".env", "uv.lock")

data = json.load(sys.stdin)
tool_input = data.get("tool_input") or {}
raw = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
# Windows paths arrive with backslashes; compare on a normalised, case-folded form.
path = str(raw).replace("\\", "/").lower()
name = path.rsplit("/", 1)[-1]

if (
    any(d in path for d in PROTECTED_DIRS)
    or name in PROTECTED_NAMES
    or ("results/" in path and name == "summary.csv")
):
    print(f"Blocked: {raw} is protected (see AGENTS.md 'Never'). Ask the human.", file=sys.stderr)
    sys.exit(2)
