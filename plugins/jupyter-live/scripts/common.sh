# Sourced by the plugin's scripts. Settings come from ~/.jupyter_mcp/config
# (KEY=VALUE lines, written by jupyter-mcp-setup); an environment variable of
# the same name overrides the file.
#
#   JUPYTER_MCP_ENV         conda env with jupyterlab + jupyter-mcp-server (required)
#   JUPYTER_ROOT            JupyterLab root; notebook paths are relative to it (default: $HOME)
#   JUPYTER_PORT            default: 8000 + uid % 1000, so users of a shared machine don't collide
#   JUPYTER_DEFAULT_KERNEL  kernel spec MCP gets when it starts one itself (default: python3)
#   WEBSOCKETS_MAX_BODY_SIZE  largest notebook (bytes) the MCP client can load (default: 256 MB)
JUPYTER_MCP_HOME="$HOME/.jupyter_mcp"
JUPYTER_MCP_CONFIG="$JUPYTER_MCP_HOME/config"
JUPYTER_MCP_TOKEN_FILE="$JUPYTER_MCP_HOME/token"

load_config() {
    local k v
    if [[ -f $JUPYTER_MCP_CONFIG ]]; then
        while IFS='=' read -r k v; do
            [[ $k =~ ^[A-Z_]+$ ]] || continue
            [[ -n ${!k:-} ]] || export "$k=$v"
        done < "$JUPYTER_MCP_CONFIG"
    fi
    export JUPYTER_ROOT="${JUPYTER_ROOT:-$HOME}"
    export JUPYTER_PORT="${JUPYTER_PORT:-$(( 8000 + $(id -u) % 1000 ))}"
    export JUPYTER_DEFAULT_KERNEL="${JUPYTER_DEFAULT_KERNEL:-python3}"
    # The nbmodel client's default 16 MB websocket limit makes larger notebooks
    # (e.g. with embedded images) silently load as empty. Releases after
    # jupyter-nbmodel-client 1.5.1 raise an error instead
    # (datalayer/jupyter-nbmodel-client#67); the limit still needs raising.
    export WEBSOCKETS_MAX_BODY_SIZE="${WEBSOCKETS_MAX_BODY_SIZE:-$((256 * 1024 * 1024))}"
}

# Exit with a pointer to setup unless config, env and token are all in place.
require_setup() {
    local why=""
    if [[ -z ${JUPYTER_MCP_ENV:-} ]]; then
        why="JUPYTER_MCP_ENV is not set"
    elif [[ ! -x $JUPYTER_MCP_ENV/bin/jupyter-mcp-server ]]; then
        why="$JUPYTER_MCP_ENV has no jupyter-mcp-server"
    elif [[ ! -s $JUPYTER_MCP_TOKEN_FILE ]]; then
        why="no token in $JUPYTER_MCP_TOKEN_FILE"
    fi
    if [[ -n $why ]]; then
        echo "jupyter-live: $why; run jupyter-mcp-setup (see the plugin README)" >&2
        exit 1
    fi
}
