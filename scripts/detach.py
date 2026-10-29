"""Run argv[1:] detached: double fork into a new session.

Done in Python since macOS has no setsid command. The program is reparented
to init, so it neither dies with the caller nor lingers as its zombie child
once stopped.
"""
import os
import sys

if os.fork() == 0:
    os.setsid()
    if os.fork() == 0:
        os.execv(sys.argv[1], sys.argv[1:])
    os._exit(0)
os.wait()
