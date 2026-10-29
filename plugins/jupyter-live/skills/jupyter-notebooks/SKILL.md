---
name: jupyter-notebooks
description: How to read, create, edit and run Jupyter notebooks (.ipynb) through the jupyter MCP server, including choosing the env (kernel) a notebook runs in. Use whenever a task touches a notebook, a Jupyter kernel, or interactive analysis with large in-memory objects.
---

# Jupyter notebooks via MCP

JupyterLab runs on the machine Claude Code runs on (a laptop, a workstation
or a cluster node), started automatically by the plugin's MCP server: one
server per user per machine. `jkernel info` shows its URL, the notebook root
and whether it is running.

## Always go through the MCP tools

- Read, create, edit and run notebooks only with the `jupyter` MCP tools
  (`use_notebook`, `read_notebook`, `insert_cell`, `edit_cell_source`,
  `execute_cell`, `execute_code`, ...). Never Read/Edit/Write/NotebookEdit a
  `.ipynb`, and never modify one from Bash. An open notebook is a live
  collaborative document: direct writes are silently discarded or overwrite
  unsaved edits, and direct reads can be stale. A hook blocks the file tools.
- If the MCP server is unavailable, say so and ask before touching the file.
  Its log is `~/.jupyter_mcp/<host>.log`. Never start the server by hand from
  a session; the user reconnects it with `/mcp`.
- Notebook paths are relative to the notebook root (`JUPYTER_ROOT`, given at
  session start and by `jkernel info`), e.g. `project/analysis.ipynb`.
  Names starting with `.` are rejected.

## Choose the env by kernel

Each env (conda env or venv) is a kernel spec; `jkernel specs` lists them
(`*` = default).

- The MCP server always requests a kernel named `python3`, which maps to the
  default kernel (`JUPYTER_DEFAULT_KERNEL`).
- For any other env: `jkernel start <spec>` prints an id, then
  `use_notebook(..., kernel_id=<id>)` or `execute_code(kernel_id=<id>)`.
- A kernel shows as "starting" until a client connects; that is not a hang.
- An env missing from `jkernel specs` needs registering once, with that env's
  Python: `<env prefix>/bin/python -m ipykernel install --user --name <name>`
  (it needs `ipykernel`; for R, `IRkernel::installspec(name = "<name>")`).
  Restart is not needed; `jkernel specs` picks it up.

## Memory

Kernels share the machine's memory (on a cluster, the job's allocation) with
everything else running there. `jkernel list` shows running kernels with their
memory use; `jkernel stop <id>` the ones you no longer need, including kernels
you started yourself.

## Notebooks vs scripts

Use notebooks for interactive exploration with large in-memory objects. For
pipeline steps, write a script and run it with the env's Python (e.g.
`conda run -n <env> python script.py`), or as a batch job on a cluster if it
outlasts or outgrows the interactive session. Execution happens on the
server, so a long cell keeps running after the Claude session ends.
