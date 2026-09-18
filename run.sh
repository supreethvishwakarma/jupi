#!/bin/bash
set -e

cd /workspaces/jupi

echo "== Killing any old Streamlit processes =="
pkill -f "streamlit run" 2>/dev/null || true
sleep 2

PORT="${PORT:-8501}"

find_free_port() {
  python - "$1" <<'PY'
import socket, sys
start = int(sys.argv[1])
for port in range(start, start + 50):
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(("0.0.0.0", port))
        print(port)
        break
    except OSError:
        pass
    finally:
        s.close()
else:
    raise SystemExit("No free port found in range")
PY
}

PORT="$(find_free_port "${PORT}")"

if [ -n "${CODESPACE_NAME:-}" ] && [ "${CODESPACES:-}" = "true" ]; then
  echo "== Codespace detected: ${CODESPACE_NAME} =="
  echo "== Forwarded URL: https://${CODESPACE_NAME}-${PORT}.app.github.dev/ =="
fi

echo "== Checking .env exists =="
if [ ! -f .env ]; then
  echo "ERROR: .env not found in /workspaces/jupi -- create it first (see earlier setup steps)."
  exit 1
fi

echo "== Starting Streamlit on port ${PORT} (detached, survives tab close) =="
nohup /workspaces/jupi/.venv/bin/python -m streamlit run app.py \
  --server.port "${PORT}" --server.address 0.0.0.0 --server.headless true \
  > streamlit.log 2>&1 &

sleep 4

if pgrep -f "streamlit run" > /dev/null; then
  echo "== Streamlit is running (PID $(pgrep -f 'streamlit run' | head -1)) =="
  echo "== Last 20 lines of streamlit.log: =="
  tail -20 streamlit.log
  echo ""
  echo "Open: http://localhost:${PORT}"
  if [ -n "${CODESPACE_NAME:-}" ] && [ "${CODESPACES:-}" = "true" ]; then
    echo "Forwarded: https://${CODESPACE_NAME}-${PORT}.app.github.dev/"
  fi
else
  echo "== Streamlit failed to start. Full log: =="
  cat streamlit.log
  exit 1
fi
