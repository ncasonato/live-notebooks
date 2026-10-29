# jupyter-hpc: Jupyter notebooks for Claude Code on the HPC

A Claude Code plugin that lets Claude read, edit and run your Jupyter notebooks
on a Slurm compute node, in any of your conda envs. It wraps
[jupyter-mcp-server](https://github.com/datalayer/jupyter-mcp-server):

- **Starts JupyterLab for you** on whatever node your job landed on, on a
  per-user port, the first time Claude needs it.
- **Keeps the token private**: it lives in `~/.jupyter_mcp/token` and never
  appears in config files or on a command line (`ps` is visible to everyone on
  the node).
- **One kernel per conda env**: `jkernel` lists, starts and stops kernels,
  with their memory use.
- **Guardrails**: a hook stops Claude from editing `.ipynb` files directly,
  which would clobber the live notebook you have open, and a skill teaches it
  the workflow.

## Install

In Claude Code:

```
/plugin marketplace add ncasonato/claude-jupyter-mcp
/plugin install jupyter-hpc@ncasonato
```

`/plugin marketplace update ncasonato` picks up new versions.

## Set up (once)

You need a conda env that runs JupyterLab and the MCP server. This is not
one of your project envs; those become kernels. Keep it out of your home
directory (10 GB quota). Either let setup create it:

```
! jupyter-mcp-setup --create --env /data/groups/<lab>/<you>/miniforge3/envs/jupyter --root /data/groups/<lab>/<you>
```

or point `--env` at an existing env that has `jupyterlab`,
`jupyter-collaboration` and `jupyter-mcp-server` (see `environment.yml`).
`--root` is the directory JupyterLab serves; notebooks must be under it.
Then run `/mcp` to reconnect the `jupyter` server. You can also just ask
Claude to set it up.

`jupyter-mcp-setup --show` prints the current settings. They are stored in
`~/.jupyter_mcp/config` and can be overridden by environment variables of
the same name: `JUPYTER_MCP_ENV`, `JUPYTER_ROOT`, `JUPYTER_PORT` (default
8000 + uid % 1000) and `JUPYTER_DEFAULT_KERNEL`.

## Make your conda envs available as kernels

From each env you want to use (it needs `ipykernel`):

```
conda run -p <env prefix> python -m ipykernel install --user --name <name>
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

To open the same JupyterLab in your browser:
`ssh -L <port>:localhost:<port> <node>`, then go to
`http://localhost:<port>/lab?token=$(cat ~/.jupyter_mcp/token)`.

## Notes

- Kernels use your Slurm job's memory. Stop the ones you no longer need.
- Cells run on the server, so long computations continue after you close
  Claude Code. The server itself ends with your job.
- The server log is `~/.jupyter_mcp/<node>.log`.
- The MCP client's websocket message limit is raised from 16 MB to 256 MB
  (`WEBSOCKETS_MAX_BODY_SIZE`): in jupyter-nbmodel-client up to 1.5.1, a
  notebook over the limit (e.g. with many embedded plots) silently opens as
  empty. Later releases raise an error instead
  ([datalayer/jupyter-nbmodel-client#67](https://github.com/datalayer/jupyter-nbmodel-client/pull/67)).
- To let Claude edit a `.ipynb` directly anyway, set
  `JUPYTER_MCP_ALLOW_DIRECT_NOTEBOOK=1` in the `env` block of
  `~/.claude/settings.json`.
