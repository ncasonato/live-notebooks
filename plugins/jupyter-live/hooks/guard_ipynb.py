"""PreToolUse hook: keep file tools off notebooks under the Jupyter root.

A notebook open in JupyterLab or an MCP session is a live collaborative
document: direct writes are silently discarded or overwrite unsaved edits, and
direct reads can be stale. Notebooks outside JUPYTER_ROOT can't be live
documents of this server (nor opened through it), so they are left alone.

Reads are denied, with a reason that points Claude to the MCP tools. Edits ask
the user, who can approve one when the MCP tools can't do it (e.g. cell tags)
and the notebook is closed everywhere. Set JUPYTER_MCP_ALLOW_DIRECT_NOTEBOOK=1
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

tool = event.get("tool_name")
procedure = (
    "If the MCP tools can't do what is needed (e.g. cell metadata or tags, "
    "notebook metadata, changing a cell's type), explain that to the user and, "
    "with their OK: unuse_notebook, make sure the notebook isn't open in "
    "JupyterLab or an editor, edit it with nbformat from Bash, then reopen it."
)
if tool == "Read":
    decision = "deny"
    reason = (
        f"Read on {path} is blocked by the jupyter-live plugin: notebooks are live "
        "collaborative documents, so read them with the jupyter MCP tools "
        "(use_notebook, read_notebook, read_cell); paths there are relative to "
        f"{root}. {procedure}"
    )
else:
    decision = "ask"
    reason = (
        f"jupyter-live: {tool} would change {path} as a file, bypassing the live "
        "notebook. Approve only if the MCP tools can't make this change and the "
        "notebook isn't open in JupyterLab, an editor or an MCP session; "
        "otherwise unsaved edits are lost or the change is overwritten."
    )

json.dump(
    {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    },
    sys.stdout,
)
