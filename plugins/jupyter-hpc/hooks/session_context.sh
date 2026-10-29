#!/usr/bin/env bash
# SessionStart hook: stdout becomes context for Claude. Says where notebooks
# live, or that setup is still to do.
. "$(dirname "${BASH_SOURCE[0]}")/../scripts/common.sh"
load_config
if [[ -z ${JUPYTER_MCP_ENV:-} || ! -x $JUPYTER_MCP_ENV/bin/jupyter-mcp-server || ! -s $JUPYTER_MCP_TOKEN_FILE ]]; then
    cat <<EOF
The jupyter-hpc plugin is installed but not set up, so its jupyter MCP server
will fail to start. If the user wants to work with notebooks, offer to run
\`jupyter-mcp-setup --env <conda env prefix> [--create] --root <notebook root>\`
(ask them for both paths; --create builds the env), then have them reconnect
with /mcp.
EOF
else
    echo "jupyter-hpc: Jupyter notebook paths in the jupyter MCP tools are relative to $JUPYTER_ROOT. Work on notebooks through those tools only (see the jupyter-notebooks skill)."
fi
