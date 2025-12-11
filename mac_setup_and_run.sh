#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────────────────────
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_DIR="$REPO_ROOT/server"
CLIENT_DIR="$REPO_ROOT/client"
SERVER_PORT="${PORT:-8000}"
CLIENT_PORT="${VITE_PORT:-5173}"
LOG_DIR="$REPO_ROOT/.logs"
PID_DIR="$REPO_ROOT/.pids"

mkdir -p "$LOG_DIR" "$PID_DIR"

SERVER_LOG="$LOG_DIR/server.log"
CLIENT_LOG="$LOG_DIR/client.log"
SERVER_PID="$PID_DIR/server.pid"
CLIENT_PID="$PID_DIR/client.pid"

# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────
info(){ echo -e "\033[34m[INFO]\033[0m  $*"; }
ok(){   echo -e "\033[32m[OK]\033[0m    $*"; }
err(){  echo -e "\033[31m[ERR]\033[0m   $*"; }

usage(){
  cat <<EOF
Uso:
  $0            # instala dependencias y arranca backend + frontend
  $0 --stop     # detiene ambos
  $0 --status   # muestra el estado y las URLs
EOF
}

# ──────────────────────────────────────────────────────────────────────────────
# PARSE ARGS
# ──────────────────────────────────────────────────────────────────────────────
CMD="run"
for a in "${@:-}"; do
  case "$a" in
    --stop)   CMD="stop" ;;
    --status) CMD="status" ;;
    -h|--help) usage; exit 0 ;;
    *) err "Argumento no reconocido: $a"; usage; exit 1 ;;
  esac
done

# ──────────────────────────────────────────────────────────────────────────────
# FUNCIONES
# ──────────────────────────────────────────────────────────────────────────────
ensure_python(){
  if ! command -v python3 >/dev/null 2>&1; then
    err "Python3 no está instalado. Instálalo con: brew install python"
    exit 1
  fi
}

setup_backend(){
  info "Verificando entorno backend (server)…"
  cd "$SERVER_DIR"
  if [[ ! -d ".venv" ]]; then
    python3 -m venv .venv
    ok "Virtualenv creado en server/.venv"
  fi
  # shellcheck disable=SC1091
  source .venv/bin/activate
  if [[ -f "requirements.txt" ]]; then
    pip install -U pip wheel
    pip install -r requirements.txt
  else
    pip install -U pip wheel
    pip install "fastapi>=0.111" "uvicorn[standard]>=0.30" "httpx>=0.27" "python-dotenv>=1.0"
  fi
  deactivate
  ok "Backend listo."
}

ensure_node(){
  if ! command -v node >/dev/null 2>&1; then
    err "Node.js no está instalado. Instálalo con: brew install node"
    exit 1
  fi
  if ! command -v npm >/dev/null 2>&1; then
    err "npm no está disponible. Instala Node (brew install node)."
    exit 1
  fi
}

setup_frontend(){
  info "Instalando dependencias frontend (client)…"
  cd "$CLIENT_DIR"
  npm install
  ok "Frontend listo."
}

start_backend(){
  info "Iniciando backend (puerto $SERVER_PORT)…"
  cd "$SERVER_DIR"
  nohup bash -lc "source .venv/bin/activate && uvicorn main:app --reload --port $SERVER_PORT" \
    >"$SERVER_LOG" 2>&1 & echo $! > "$SERVER_PID"
  sleep 0.5
  ok "Backend corriendo (PID $(cat "$SERVER_PID")). Log: $SERVER_LOG"
}

start_frontend(){
  info "Iniciando frontend (puerto $CLIENT_PORT)…"
  cd "$CLIENT_DIR"
  nohup bash -lc "npm run dev -- --port $CLIENT_PORT" \
    >"$CLIENT_LOG" 2>&1 & echo $! > "$CLIENT_PID"
  sleep 0.5
  ok "Frontend corriendo (PID $(cat "$CLIENT_PID")). Log: $CLIENT_LOG"
}

stop_if_running(){
  local name="$1" pidfile="$2"
  if [[ -f "$pidfile" ]]; then
    local pid; pid="$(cat "$pidfile" || echo "")"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      info "Deteniendo $name (PID $pid)…"
      kill "$pid" 2>/dev/null || true
      sleep 0.5
      if kill -0 "$pid" 2>/dev/null; then
        info "Forzando cierre de $name…"
        kill -9 "$pid" 2>/dev/null || true
      fi
      ok "$name detenido."
    fi
    rm -f "$pidfile"
  fi
}

status(){
  echo "── STATUS ────────────────────────────────"
  if [[ -f "$SERVER_PID" ]] && kill -0 "$(cat "$SERVER_PID")" 2>/dev/null; then
    echo "Backend : RUNNING (PID $(cat "$SERVER_PID")) http://127.0.0.1:$SERVER_PORT/health"
  else
    echo "Backend : STOPPED"
  fi
  if [[ -f "$CLIENT_PID" ]] && kill -0 "$(cat "$CLIENT_PID")" 2>/dev/null; then
    echo "Frontend: RUNNING (PID $(cat "$CLIENT_PID")) http://localhost:$CLIENT_PORT/"
  else
    echo "Frontend: STOPPED"
  fi
  echo "Logs en: $LOG_DIR"
}

# ──────────────────────────────────────────────────────────────────────────────
# COMANDOS
# ──────────────────────────────────────────────────────────────────────────────
if [[ "$CMD" == "stop" ]]; then
  stop_if_running "backend" "$SERVER_PID"
  stop_if_running "frontend" "$CLIENT_PID"
  status
  exit 0
fi

if [[ "$CMD" == "status" ]]; then
  status
  exit 0
fi

# run (por defecto)
[[ -d "$SERVER_DIR" ]] || { err "No existe server/ en $REPO_ROOT"; exit 1; }
[[ -d "$CLIENT_DIR" ]] || { err "No existe client/ en $REPO_ROOT"; exit 1; }

ensure_python
setup_backend
ensure_node
setup_frontend

stop_if_running "backend" "$SERVER_PID" || true
stop_if_running "frontend" "$CLIENT_PID" || true

start_backend
start_frontend

echo
echo "── URLs ──────────────────────────────────"
echo "Backend : http://127.0.0.1:$SERVER_PORT/health"
echo "Frontend: http://localhost:$CLIENT_PORT/"
echo
echo "Comandos:"
echo "  ./mac_run_project.sh --status   # ver estado"
echo "  ./mac_run_project.sh --stop     # detener ambos"
echo "  tail -f $LOG_DIR/server.log     # ver log backend"
echo "  tail -f $LOG_DIR/client.log     # ver log frontend"