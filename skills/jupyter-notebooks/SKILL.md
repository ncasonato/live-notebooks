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
  `execute_cell`, `execute_code`, ...), and create them with
  `use_notebook(mode="create")`. Don't Read/Edit/Write/NotebookEdit a `.ipynb`
  under the notebook root, or modify one from Bash, except as below. An open
  notebook is a live collaborative document: direct writes are silently
  discarded or overwrite unsaved edits, and direct reads can be stale. A hook
  denies the file tools there.
- Notebooks outside the notebook root can't be opened through MCP; treat them
  as ordinary files.
- If the MCP server is unavailable, say so and ask before touching the file.
  Its log is `~/.jupyter_mcp/<host>.log`. Never start the server by hand from
  a session; the user reconnects it with `/mcp`.
- Notebook paths are relative to the notebook root (`JUPYTER_ROOT`, given at
  session start and by `jkernel info`), e.g. `project/analysis.ipynb`.
  Names starting with `.` are rejected. `use_notebook(mode="create")` fails
  if the folder doesn't exist yet: create it first with `mkdir -p` under the
  root.

## Bulk edits, and what the MCP tools can't do

The tools work one cell at a time (`edit_cell_source` is a find-and-replace
within a single cell). That is the right route for a handful of cells. Use
the file route below instead when:

- the change spans many cells or several notebooks (a rename across a
  notebook, the same first cell added to every notebook, renumbering
  sections), where cell-by-cell calls would be slow and error-prone;
- the tools can't do it at all: cell metadata or tags (e.g. Jupyter Book's
  `remove-input`, `hide-cell`), notebook metadata (kernelspec, title), an
  existing cell's type (or delete and re-insert it) and attachments.

File route:

1. Tell the user what you're about to change and why it isn't going through
   MCP, and ask before going on.
2. `unuse_notebook` for each notebook involved, and confirm with the user
   that none is open in JupyterLab or an editor, so no live copy with unsaved
   edits can overwrite the change.
3. Edit the files with one `nbformat` script from Bash (it validates the
   result), using the server env's Python (`jkernel info` shows the env).
   Print what changed per notebook.
4. `use_notebook` again and check the result with `read_notebook`; the
   server picks up the changed files.

## Choose the env by kernel

Each env (conda env or venv) is a kernel spec; `jkernel specs` lists them
(`*` = default).

- The MCP server always requests a kernel named `python3`, which maps to the
  default kernel (`JUPYTER_DEFAULT_KERNEL`). Unless the user changed it, that
  is the server env itself: Jupyter only, no numpy, pandas or matplotlib.
  Use it for plain Python, not analysis. For analysis, pick the project's env
  from `jkernel specs`; if none fits, say so and suggest registering one (or
  setting it as the default with `live-notebooks-setup --default-kernel`),
  rather than installing packages into the server env.
- For any other env: `jkernel start <spec>` prints an id, then
  `use_notebook(..., kernel_id=<id>)` or `execute_code(kernel_id=<id>)`.
- A kernel shows as "starting" until a client connects; that is not a hang.
- An env missing from `jkernel specs` needs registering once, with that env's
  Python: `<env prefix>/bin/python -m ipykernel install --user --name <name>`
  (it needs `ipykernel`; for R, `IRkernel::installspec(name = "<name>")`).
  Restart is not needed; `jkernel specs` picks it up.

## Plots

Plot outputs come back as images. Run `%matplotlib inline` in a kernel before
its first plot: with some version mixes (e.g. matplotlib < 3.9 with IPython 9)
the first figure of a fresh kernel otherwise comes back only as text like
`<Figure size 640x480 with 1 Axes>`. If that happens, run the cell again.

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
