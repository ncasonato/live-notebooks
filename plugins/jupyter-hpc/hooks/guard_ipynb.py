"""PreToolUse hook: deny file tools on .ipynb files.

A notebook open in JupyterLab or an MCP session is a live collaborative
document: direct writes are silently discarded or overwrite unsaved edits, and
direct reads can be stale. Set JUPYTER_MCP_ALLOW_DIRECT_NOTEBOOK=1 (e.g. in the
"env" block of settings.json) to switch this off.
"""
import json
import os
import sys

if os.environ.get("JUPYTER_MCP_ALLOW_DIRECT_NOTEBOOK") == "1":
    sys.exit(0)

event = json.load(sys.stdin)
args = event.get("tool_input") or {}
path = args.get("file_path") or args.get("notebook_path") or ""
if not path.endswith(".ipynb"):
    sys.exit(0)

reason = (
    f"{event.get('tool_name')} on {path} is blocked by the jupyter-hpc plugin: "
    "notebooks are live collaborative documents, so read, edit and run them "
    "through the jupyter MCP tools (use_notebook, read_notebook, "
    "edit_cell_source, insert_cell, execute_cell, ...). Notebook paths there are "
    "relative to the Jupyter root (`jkernel info`). If the MCP server is "
    "unavailable, tell the user and ask before touching the file."
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
