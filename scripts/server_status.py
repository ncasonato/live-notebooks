"""Exit 0 if our Jupyter server answers at JUPYTER_URL, 1 if nothing is
listening, 2 if the port is held by someone else (or rejects our token).

Run by mcp-wrapper with the server env's python; JUPYTER_URL and
JUPYTER_TOKEN come from the environment.
"""
import os
import sys
import urllib.error
import urllib.request

req = urllib.request.Request(
    os.environ["JUPYTER_URL"] + "/api/status",
    headers={"Authorization": "token " + os.environ["JUPYTER_TOKEN"]},
)
try:
    urllib.request.urlopen(req, timeout=3)
except urllib.error.HTTPError:
    sys.exit(2)
except Exception:
    sys.exit(1)
