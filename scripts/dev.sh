#!/usr/bin/env bash
# Start the Axplorer backend (uvicorn, :8050 with --reload) and the Vite dev
# server together. Vite's /api proxy targets :8050, so both must be up for the
# dashboard to work in dev mode. Ctrl-C stops both.

set -u
# Run each child in its own process group so we can signal the whole tree
# (npm spawns sh, which spawns vite -- a plain SIGTERM on npm orphans vite).
set -m

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PORT=8050

cd "$REPO_ROOT"

# Prefer the repo venv's python if present. We invoke `python -m uvicorn`
# rather than `.venv/bin/uvicorn` because pip-installed console scripts embed
# the venv path in their shebang, and that path breaks if the project
# directory is moved. Running the interpreter directly is move-safe.
PY="uvicorn"
if [[ -x ".venv/bin/python" ]]; then
  PY=".venv/bin/python -m uvicorn"
  echo "[dev] using .venv/bin/python"
fi

backend_pid=""
frontend_pid=""

kill_group() {
  local pid="$1"
  [[ -z "$pid" ]] && return 0
  kill -0 "$pid" 2>/dev/null || return 0
  # Negative PID sends to the whole process group.
  kill -TERM "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
}

cleanup() {
  trap - INT TERM EXIT
  kill_group "$frontend_pid"
  kill_group "$backend_pid"
  wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

# Pre-flight: make sure nothing else owns :8050. Vite proxies /api there, so a
# foreign listener (e.g. another lab app) would silently shadow our backend.
if (exec 3<>/dev/tcp/127.0.0.1/"$BACKEND_PORT") 2>/dev/null; then
  echo "[dev] port ${BACKEND_PORT} already in use -- stop the other listener and retry." >&2
  echo "[dev] see:  ss -tlnp | grep ':${BACKEND_PORT} '" >&2
  exit 1
fi

echo "[dev] starting backend: ${PY} api.app:app --port ${BACKEND_PORT} --reload"
# shellcheck disable=SC2086
$PY api.app:app --host 127.0.0.1 --port "$BACKEND_PORT" --reload &
backend_pid=$!

# Wait (up to ~20s) for backend to accept connections before starting Vite.
backend_ready=""
for _ in $(seq 1 40); do
  if ! kill -0 "$backend_pid" 2>/dev/null; then
    echo "[dev] backend exited before it was ready -- aborting" >&2
    exit 1
  fi
  if (exec 3<>/dev/tcp/127.0.0.1/"$BACKEND_PORT") 2>/dev/null; then
    echo "[dev] backend: OK (${BACKEND_PORT})"
    backend_ready=1
    break
  fi
  sleep 0.5
done

if [[ -z "$backend_ready" ]]; then
  echo "[dev] backend did not become ready on :${BACKEND_PORT} after 20s -- aborting" >&2
  exit 1
fi

echo "[dev] starting frontend: npm --prefix web run dev"
echo "[dev] Vite binds all interfaces -- use its printed Network URL from other devices"
npm --prefix web run dev &
frontend_pid=$!

# Exit as soon as either child exits; cleanup trap handles the survivor.
wait -n "$backend_pid" "$frontend_pid"
