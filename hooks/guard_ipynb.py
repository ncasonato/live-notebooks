"""PreToolUse hook: keep file tools off notebooks under the Jupyter root.

A notebook open in JupyterLab or an MCP session is a live collaborative
document: direct writes are silently discarded or overwrite unsaved edits, and
direct reads can be stale. Notebooks outside JUPYTER_ROOT can't be live
documents of this server (nor opened through it), so they are left alone.

All file tools are denied, with a reason that points Claude to the MCP tools
and, for what they can't do (e.g. cell tags), to the nbformat procedure.
Asking the user instead is pointless: Claude Code won't edit a notebook it
hasn't Read, so only Write of a new notebook could reach the prompt, and that
belongs in use_notebook(mode="create"). Set JUPYTER_MCP_ALLOW_DIRECT_NOTEBOOK=1
(e.g. in the "env" block of settings.json) to switch this off.
"""
import json
import os
import re
import sys
from pathlib import Path

if os.environ.get("JUPYTER_MCP_ALLOW_DIRECT_NOTEBOOK") == "1":
    sys.exit(0)

event = json.load(sys.stdin)
args = event.get("tool_input") or {}
path = args.get("file_path") or args.get("notebook_path") or ""
if not path.endswith(".ipynb"):
    sys.exit(0)


def jupyter_root():
    # Same rules as scripts/common.sh: the config file, overridden by env vars.
    root = os.environ.get("JUPYTER_ROOT")
    config = Path.home() / ".jupyter_mcp" / "config"
    if not root and config.exists():
        for line in config.read_text().splitlines():
            m = re.fullmatch(r"JUPYTER_ROOT=(.*)", line)
            if m:
                root = m.group(1)
    return Path(root or Path.home()).resolve()


target = (Path(event.get("cwd") or ".") / path).resolve()
root = jupyter_root()
if target != root and root not in target.parents:
    sys.exit(0)

reason = (
    f"{event.get('tool_name')} on {path} is blocked by the live-notebooks plugin: "
    "notebooks are live collaborative documents, so read, create, edit and run "
    "them with the jupyter MCP tools (use_notebook, read_notebook, read_cell, "
    "insert_cell, edit_cell_source, ...); paths there are relative to "
    f"{root}. For bulk edits across many cells or notebooks, or what the MCP "
    "tools can't do (e.g. cell metadata or tags, notebook metadata), explain "
    "that to the user and, with their OK: "
    "unuse_notebook, make sure the notebook isn't open in JupyterLab or an "
    "editor, edit it with nbformat from Bash, then reopen it."
)
json.dump(
    {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    },
    sys.stdout,
)
