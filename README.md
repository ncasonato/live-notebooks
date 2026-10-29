![](icon.svg)

# Live Notebooks for Jupyter

A Claude Code plugin that lets Claude work in your Jupyter notebooks the way
you do, with a running kernel, instead of only reading and editing the saved
`.ipynb` file. It wraps
[jupyter-mcp-server](https://github.com/datalayer/jupyter-mcp-server), so
Claude can:

- **run cells** one at a time and in whatever order it needs, and **see the
  outputs**, plots included;
- **keep objects in kernel memory** between steps instead of reloading data;
- **use any of your envs** (conda or venv) as the kernel;
- **edit the notebook live**: if you have it open in JupyterLab, you see its
  changes as they happen.

What the plugin adds on top of the server:

- **Starts JupyterLab for you** on the machine Claude Code runs on, on a
  per-user port, the first time Claude needs it.
- **Keeps the token private**: on a shared machine, other users can reach
  your JupyterLab on `127.0.0.1`; the token is what keeps them out. It lives
  in `~/.jupyter_mcp/token`, readable only by you, and never appears in
  config files or on a command line, where other users could see it with
  `ps`.
- **`jkernel`** to list, start and stop kernels, with their memory use.
- **Guardrails**: for notebooks under the notebook root, a hook stops Claude
  from reading or editing `.ipynb` files as text, which would clobber the
  live notebook you have open. A skill teaches it the workflow, including a
  safe way, with your OK, to make bulk edits across many cells or notebooks
  and the few changes the MCP tools can't (cell tags, notebook metadata).

Works on Linux and macOS, on a laptop or a remote machine such as an HPC
cluster node. On Windows, use WSL with Claude Code running inside it; native
Windows isn't supported. The hooks and `jkernel` need `python3` on your PATH.
It is a Claude Code plugin: claude.ai chat and Cowork can't install it.

## Install

In a terminal:

```
claude plugin marketplace add ncasonato/live-notebooks
claude plugin install live-notebooks@ncasonato
```

then restart Claude Code. In the terminal version of Claude Code you can
use `/plugin marketplace add …` and `/plugin install …` instead; the VS Code
extension has no `/plugin` command.

To update:

```
claude plugin marketplace update ncasonato
claude plugin update live-notebooks@ncasonato
```

then restart Claude Code or run `/reload-plugins`.

If you installed it under its earlier names (`jupyter-hpc` or
`jupyter-live`), the marketplace update moves your settings to
`live-notebooks`. If the plugin then shows as not installed, run
`claude plugin install live-notebooks@ncasonato`; your setup in
`~/.jupyter_mcp` is kept.

## Set up (once)

Ask Claude to set it up, e.g. "set up live-notebooks for my notebooks in
~/projects". It runs `live-notebooks-setup --create --root ~/projects`,
asking you first which env manager to use if you have several. Then
reconnect the `jupyter` server with `/mcp`, or restart Claude Code.
`--root` is the directory JupyterLab serves; notebooks must be under it.

The plugin's commands (`live-notebooks-setup`, `jkernel`) are on PATH only
inside Claude Code. To use them in your own terminal too, ask Claude to run
`live-notebooks-setup --link`: it puts launchers in `~/.local/bin` that
always run the installed version.

`--create` builds a small server env that runs JupyterLab and the MCP
server, in `~/.jupyter_mcp/env` (`--env PATH` to put it elsewhere). This is
not one of your project envs; those become kernels. Pick how it is built with
`--with`:

- `--with conda`: conda/mamba, from `environment.yml`;
- `--with uv`: [uv](https://docs.astral.sh/uv/), which downloads Python
  itself if needed;
- `--with venv`: a venv from Python 3.10 or newer, from `requirements.txt`.

Without `--with`, setup uses the first of these it finds. When Claude sets it
up, it asks which you prefer if more than one is installed. On a Mac with none
of them, `brew install uv` is enough.

To use an existing env instead, leave out `--create` and pass `--env PATH`:
it needs `jupyterlab`, `jupyter-collaboration` and `jupyter-mcp-server`.

`live-notebooks-setup --show` prints the current settings. They are stored in
`~/.jupyter_mcp/config` and can be overridden by environment variables of
the same name: `JUPYTER_MCP_ENV`, `JUPYTER_ROOT`, `JUPYTER_PORT` (default
8000 + uid % 1000), `JUPYTER_DEFAULT_KERNEL` and `WEBSOCKETS_MAX_BODY_SIZE`
(bytes; set with `--max-notebook-mb`, see Notes).

## Make your envs available as kernels

With each env you want to use (it needs `ipykernel`):

```
<env prefix>/bin/python -m ipykernel install --user --name <name>
```

Use `IRkernel::installspec(name = "<name>")` for R. Then `jkernel specs` lists
it. Set `--default-kernel <name>` if most of your work is in one env: that is
the kernel Claude gets when it does not pick one. Out of the box the default
is the server env itself, which has Jupyter but no numpy, pandas or
matplotlib, so register at least one analysis env.

## Use

Just ask Claude to work in a notebook, e.g. "open `project/analysis.ipynb`
with the `scanpy` kernel and plot the UMAP". Claude runs `jkernel` itself;
you can too, in your terminal after `live-notebooks-setup --link`:

| Command | |
|---|---|
| `jkernel info` | server URL, notebook root, env, whether it runs |
| `jkernel specs` | available kernels (one per env) |
| `jkernel list` | running kernels with memory use |
| `jkernel start <spec>` / `jkernel stop <id>` | start / stop a kernel |

To open the same JupyterLab in your browser, go to
`http://localhost:<port>/lab?token=<token>` (`jkernel info` shows the URL;
the token is in `~/.jupyter_mcp/token`).

## On an HPC cluster

The plugin was built for running Claude Code (e.g. in VS Code) inside an
interactive Slurm job, and handles that without extra setup:

- Each compute node gets its own JupyterLab, started on whichever node your
  job lands on. The per-user port keeps users on the same node apart, and the
  server ends with your job.
- Keep the env and caches off your home directory if it has a small quota:
  `--env /data/<group>/<you>/envs/live-notebooks`.
- Kernels count against your job's memory: check `jkernel list`.
- To reach JupyterLab from your laptop:
  `ssh -L <port>:localhost:<port> <node>`, then open the URL above.

## What it runs, stores and sends

- **Processes.** The first time Claude uses the notebook tools,
  `scripts/mcp-wrapper` starts JupyterLab from the server env, listening on
  `127.0.0.1` only, detached so it keeps running across Claude sessions until
  you stop it or the machine (or Slurm job) ends. It then runs
  `jupyter-mcp-server`, which talks to Claude Code over stdio. Kernels start
  only when you or Claude start one; code in a notebook runs with your user's
  permissions, like any notebook you run yourself.
- **Files.** Everything goes in `~/.jupyter_mcp/`: `config`, `token` (mode
  600), one log per host (warnings only, restarted past 5 MB), a copy of the
  default kernel's spec in `share/`, and the server env in `env/` if setup
  created it there. `live-notebooks-setup --link` also writes two small
  launchers to `~/.local/bin` (or the folder you give). Notebooks are
  written only under the notebook root, through Jupyter.
- **Token.** Generated locally by setup and used only to authenticate to the
  local JupyterLab.
- **Network.** JupyterLab, the MCP server and `jkernel` only talk to each
  other over `127.0.0.1`. There is no telemetry, and nothing is sent to any
  other host. The one download is `live-notebooks-setup --create`, run by you
  or by Claude with your OK, which installs the pinned packages from
  conda-forge or PyPI (and uv may download a Python build).
- **Hooks.** At session start, a hook tells Claude the notebook root, or that
  setup is still to do and which env managers are installed. Before each
  file tool call, a hook denies Read, Write, Edit and NotebookEdit on `.ipynb`
  files under the notebook root, pointing Claude to the notebook tools.

## Notes

- Kernels share the machine's memory. Stop the ones you no longer need.
- Cells run on the server, so long computations continue after you close
  Claude Code.
- The server log is `~/.jupyter_mcp/<host>.log`. It records warnings and
  errors only; past 5 MB it is moved to `<host>.log.old` when the server next
  starts.
- The MCP client's websocket message limit is raised from 16 MB to 256 MB
  (`WEBSOCKETS_MAX_BODY_SIZE`): in jupyter-nbmodel-client up to 1.5.1, a
  notebook over the limit (e.g. with many embedded plots) silently opens as
  empty. Later releases raise an error instead
  ([datalayer/jupyter-nbmodel-client#67](https://github.com/datalayer/jupyter-nbmodel-client/pull/67)).
  For bigger notebooks, raise it with `live-notebooks-setup --max-notebook-mb N`
  and reconnect with `/mcp`.
- If the first plot in a kernel shows up as `<Figure size … with 1 Axes>`
  instead of an image, run `%matplotlib inline` first (Claude does this
  itself). It happens with some version mixes, e.g. matplotlib older than 3.9
  with IPython 9, in JupyterLab too.
- To switch the notebook guard off entirely, set
  `JUPYTER_MCP_ALLOW_DIRECT_NOTEBOOK=1` in the `env` block of
  `~/.claude/settings.json`.

## Not affiliated with Project Jupyter

Live Notebooks for Jupyter is an independent, free plugin that uses Jupyter software
(JupyterLab, and [jupyter-mcp-server](https://github.com/datalayer/jupyter-mcp-server)
by Datalayer). It is not made, sponsored or endorsed by Project Jupyter.
"Jupyter" is a trademark of LF Charities.
