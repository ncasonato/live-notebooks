"""Write a copy of kernel spec argv[1] to argv[2] as kernel.json.

Run by start-jupyter with the server env's python, to shadow "python3".
"""
import json
import sys

from jupyter_client.kernelspec import KernelSpecManager

name, out = sys.argv[1], sys.argv[2]
spec = KernelSpecManager().get_kernel_spec(name).to_dict()
spec["display_name"] += " [default]"
with open(out, "w") as f:
    json.dump(spec, f, indent=1)
