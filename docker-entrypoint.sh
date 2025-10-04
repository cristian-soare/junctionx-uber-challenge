#!/bin/bash
set -e

cd /workspace/server && hatch run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
cd /workspace/client && bun run dev --host 0.0.0.0 &

wait -n

exit $?
