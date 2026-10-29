<img src="icon.svg" alt="" width="96" align="right">

# jupyter-live: live Jupyter notebooks for Claude Code

A Claude Code plugin that lets Claude work in your Jupyter notebooks the way
you do, instead of editing `.ipynb` files as text. It wraps
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
- **Keeps the token private**: it lives in `~/.jupyter_mcp/token` and never
  appears in config files or on a command line (visible to every user of a
  shared machine through `ps`).
- **`jkernel`** to list, start and stop kernels, with their memory use.
- **Guardrails**: a hook stops Claude from editing `.ipynb` files directly,
  which would clobber the live notebook you have open, and a skill teaches it
  the workflow.

Works on Linux and macOS (and WSL), on a laptop or a remote machine such as an
HPC cluster node. The hooks and `jkernel` need `python3` on your PATH.

## Install

In Claude Code:

```
/plugin marketplace add ncasonato/claude-jupyter-mcp
/plugin install jupyter-live@ncasonato
```

`/plugin marketplace update ncasonato` picks up new versions.

## Set up (once)

The easiest way is to ask Claude to set it up. Or run, inside Claude Code:

```
! jupyter-live-setup --create --root ~/projects
```

then `/mcp` to reconnect the `jupyter` server. `--root` is the directory
JupyterLab serves; notebooks must be under it.

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

`jupyter-live-setup --show` prints the current settings. They are stored in
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
the kernel Claude gets when it does not pick one.

## Use

Just ask Claude to work in a notebook, e.g. "open `project/analysis.ipynb`
with the `scanpy` kernel and plot the UMAP". Claude can run `jkernel` itself,
and inside Claude Code you can run it with a leading `!`:

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
  `--env /data/<group>/<you>/envs/jupyter-live`.
- Kernels count against your job's memory: check `jkernel list`.
- To reach JupyterLab from your laptop:
  `ssh -L <port>:localhost:<port> <node>`, then open the URL above.

## Notes

- Kernels share the machine's memory. Stop the ones you no longer need.
- Cells run on the server, so long computations continue after you close
  Claude Code.
- The server log is `~/.jupyter_mcp/<host>.log`.
- The MCP client's websocket message limit is raised from 16 MB to 256 MB
  (`WEBSOCKETS_MAX_BODY_SIZE`): in jupyter-nbmodel-client up to 1.5.1, a
  notebook over the limit (e.g. with many embedded plots) silently opens as
  empty. Later releases raise an error instead
  ([datalayer/jupyter-nbmodel-client#67](https://github.com/datalayer/jupyter-nbmodel-client/pull/67)).
  For bigger notebooks, raise it with `jupyter-live-setup --max-notebook-mb N`
  and reconnect with `/mcp`.
- To let Claude edit a `.ipynb` directly anyway, set
  `JUPYTER_MCP_ALLOW_DIRECT_NOTEBOOK=1` in the `env` block of
  `~/.claude/settings.json`.
