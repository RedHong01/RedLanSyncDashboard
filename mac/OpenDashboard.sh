#!/bin/zsh
set -u

ROOT_DIR=""
CONFIG_PATH=""
TIMEOUT_SECONDS=3

while [[ $# -gt 0 ]]; do
    case "$1" in
        --root)
            ROOT_DIR="$2"
            shift 2
            ;;
        --config)
            CONFIG_PATH="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT_SECONDS="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

SCRIPT_PATH="$0"
case "$SCRIPT_PATH" in
    /*) ;;
    *) SCRIPT_PATH="$PWD/$SCRIPT_PATH" ;;
esac
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" >/dev/null 2>&1 && pwd -P)"

if [[ -z "$ROOT_DIR" ]]; then
    if [[ -f "$SCRIPT_DIR/../server.py" ]]; then
        ROOT_DIR="$(cd "$SCRIPT_DIR/.." >/dev/null 2>&1 && pwd -P)"
    else
        ROOT_DIR="$HOME/Library/Application Support/RedLanSyncDashboard"
    fi
fi

if [[ -z "$CONFIG_PATH" ]]; then
    if [[ -f "$ROOT_DIR/config.json" ]]; then
        CONFIG_PATH="$ROOT_DIR/config.json"
    elif [[ -f "$HOME/Library/Application Support/RedLanSyncDashboard/config.json" ]]; then
        CONFIG_PATH="$HOME/Library/Application Support/RedLanSyncDashboard/config.json"
    else
        CONFIG_PATH="$ROOT_DIR/config.json"
    fi
fi

python_bin="$(command -v python3 || true)"
if [[ -z "$python_bin" ]]; then
    /usr/bin/open "http://127.0.0.1:8765/"
    exit 0
fi

config_json="$("$python_bin" - "$CONFIG_PATH" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1]).expanduser()
defaults = {
    "listen_port": 8765,
    "dashboard_alias": "red-lan-sync.local",
    "mac_ip": "",
    "shared_token": "",
}
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    data = {}
defaults.update(data)
print(json.dumps(defaults))
PY
)"

listen_port="$("$python_bin" -c 'import json,sys; print(json.loads(sys.argv[1]).get("listen_port") or 8765)' "$config_json")"
dashboard_alias="$("$python_bin" -c 'import json,sys; print(json.loads(sys.argv[1]).get("dashboard_alias") or "")' "$config_json")"
mac_ip="$("$python_bin" -c 'import json,sys; print(json.loads(sys.argv[1]).get("mac_ip") or "")' "$config_json")"
shared_token="$("$python_bin" -c 'import json,sys; print(json.loads(sys.argv[1]).get("shared_token") or "")' "$config_json")"

candidate_urls=""
append_candidate() {
    local url="$1"
    if [[ -n "$url" ]] && ! printf "%s\n" "$candidate_urls" | /usr/bin/grep -Fxq "$url"; then
        candidate_urls="${candidate_urls}${url}
"
    fi
}

append_candidate "http://127.0.0.1:${listen_port}"
if [[ -n "$dashboard_alias" ]]; then
    append_candidate "http://${dashboard_alias}:${listen_port}"
fi
if [[ -n "$mac_ip" ]]; then
    append_candidate "http://${mac_ip}:${listen_port}"
fi

try_start_service() {
    /bin/launchctl kickstart -k "gui/$UID/com.redwang.lansyncdashboard" >/dev/null 2>&1 || true
}

is_dashboard_reachable() {
    local url="$1"
    /usr/bin/curl --silent --fail --max-time "$TIMEOUT_SECONDS" "${url%/}/api/config" >/dev/null 2>&1
}

auth_url() {
    local base_url="$1"
    if [[ -z "$shared_token" ]]; then
        printf "%s/\n" "${base_url%/}"
        return
    fi
    "$python_bin" - "$base_url" "$shared_token" <<'PY'
import sys
from urllib.parse import quote

base = sys.argv[1].rstrip("/")
token = quote(sys.argv[2], safe="")
print(f"{base}/auth?token={token}")
PY
}

open_first_reachable() {
    local url
    while IFS= read -r url; do
        [[ -z "$url" ]] && continue
        if is_dashboard_reachable "$url"; then
            /usr/bin/open "$(auth_url "$url")"
            return 0
        fi
    done <<EOF
$candidate_urls
EOF
    return 1
}

if open_first_reachable; then
    exit 0
fi

try_start_service
/bin/sleep 2
if open_first_reachable; then
    exit 0
fi

message="Red LAN Sync Dashboard is not reachable.

Tried:
$(printf "%s" "$candidate_urls" | sed '/^$/d' | sed 's/^/- /')

Check that the Mac service is installed and running, then try again."

if command -v osascript >/dev/null 2>&1; then
    /usr/bin/osascript -e 'display dialog "'"${message//\"/\\\"}"'" buttons {"OK"} default button "OK" with icon caution' >/dev/null 2>&1 || true
else
    printf "%s\n" "$message"
fi

exit 1
