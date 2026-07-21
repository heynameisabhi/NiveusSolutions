#!/bin/sh
# ─── entrypoint.sh ───────────────────────────────────────────────────────────
# Runs as root to fix mounted volume permissions, then drops to appuser.
# This is necessary because Docker named volumes are owned by root on creation
# and override any chown done during the image build.
# ─────────────────────────────────────────────────────────────────────────────
set -e

# Fix ownership of the mounted /data volume so appuser can write the SQLite DB
chown -R appuser:appgroup /data

# Drop privileges and exec the main process (PID 1)
exec gosu appuser "$@"
