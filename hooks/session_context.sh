#!/usr/bin/env bash
# SessionStart hook: stdout becomes context for Claude. Says where notebooks
# live, or that setup is still to do and which env managers it can use.
. "$(dirname "${BASH_SOURCE[0]}")/../scripts/common.sh"
load_config
if [[ -n ${JUPYTER_MCP_ENV:-} && -x $JUPYTER_MCP_ENV/bin/jupyter-mcp-server && -s $JUPYTER_MCP_TOKEN_FILE ]]; then
    echo "live-notebooks: Jupyter notebook paths in the jupyter MCP tools are relative to $JUPYTER_ROOT. Work on notebooks through those tools only (see the jupyter-notebooks skill)."
    exit 0
fi

found=""
conda=$(conda_exe)
[[ -n $conda ]] && found+="  - conda: $conda (--with conda)"$'\n'
command -v uv > /dev/null && found+="  - uv: $(command -v uv) (--with uv)"$'\n'
py=$(python_310)
[[ -n $py ]] && found+="  - venv from $(command -v "$py") (--with venv)"$'\n'

cat <<EOF
The live-notebooks plugin is installed but not set up, so its jupyter MCP server
will fail to start. If the user wants to work with notebooks, offer to run
setup for them:

    live-notebooks-setup --create --with <manager> --root /path/to/notebooks

- --root is the folder their notebooks live under (often the current
  project); confirm it with the user and pass a real absolute path, never a
  placeholder.
- --create builds a small dedicated server env (JupyterLab +
  jupyter-mcp-server) in ~/.jupyter_mcp/env. It is not the analysis env: the
  user's project envs become kernels later. Add --env /some/path only if the
  user wants it elsewhere (e.g. off a small home quota), or, without
  --create, to reuse an existing server env.
- It takes a few minutes; run it with a generous timeout. Afterwards the user
  reconnects with /mcp (or starts a new session).
EOF
if [[ -z $found ]]; then
    cat <<EOF
- No env manager was found here (no conda/mamba, no uv, no Python >= 3.10).
  Tell the user they need one first, e.g. uv (\`brew install uv\` on macOS, or
  https://docs.astral.sh/uv/) or Miniforge, and to run the installer
  themselves since it changes their shell setup.
EOF
elif (( $(printf '%s' "$found" | grep -c .) > 1 )); then
    printf -- '- Env managers found here; ask the user which they prefer:\n%s' "$found"
else
    printf -- '- Env manager found here (only one, so use it and say so):\n%s' "$found"
fi
