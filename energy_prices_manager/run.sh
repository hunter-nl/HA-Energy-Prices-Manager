#!/usr/bin/env sh
set -eu

child_pid=""

shutdown() {
    if [ -n "$child_pid" ]; then
        kill -TERM "$child_pid" 2>/dev/null || true
        wait "$child_pid" || true
    fi
    exit 0
}

trap shutdown TERM INT

uvicorn app.main:app --host 0.0.0.0 --port 8099 &
child_pid=$!
wait "$child_pid"
