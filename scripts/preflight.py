#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path
import socket
import sys
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dependency_auditor import endpoint_inventory
CONFIG = ROOT / "config.json"
EXAMPLE_CONFIG = ROOT / "config.example.json"
REQUIRED_WINDOWS_FILES = [
    "LanSyncAgent.ps1",
    "DependencyScan.ps1",
    "OpenDashboard.ps1",
    "install-agent.ps1",
]


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def check_path(path: Path, label: str) -> dict:
    return {"label": label, "path": str(path), "ok": path.exists()}


def can_connect(url: str, timeout: int = 3) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return {"url": url, "ok": 200 <= response.status < 300, "status": response.status}
    except Exception as exc:
        return {"url": url, "ok": False, "error": str(exc)}


def local_ip_candidates() -> list[str]:
    addresses = []
    try:
        for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            address = item[4][0]
            if not address.startswith("127.") and address not in addresses:
                addresses.append(address)
    except OSError:
        pass
    return addresses


def config_placeholders(config: dict) -> list[str]:
    placeholders = []
    for key, value in config.items():
        text = str(value)
        if "YOUR_" in text or "AAAAAAA" in text or "IIIIIII" in text or text in {"192.168.0.50", "192.168.0.10", "00:11:22:33:44:55", "aa:bb:cc:dd:ee:ff"}:
            placeholders.append(key)
    return placeholders


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether a cloned SystemSync repo is ready to deploy.")
    parser.add_argument("--json", action="store_true", help="Print JSON only.")
    parser.add_argument("--timeout", type=int, default=3, help="HTTP timeout in seconds.")
    args = parser.parse_args()

    config = load_json(CONFIG)
    example = load_json(EXAMPLE_CONFIG)
    effective = dict(example)
    effective.update(config)
    port = int(effective.get("listen_port") or 8765)
    syncthing_url = str(effective.get("syncthing_url") or "http://127.0.0.1:8384").rstrip("/")
    inventory = endpoint_inventory()

    checks = [
        {"label": "python_version", "ok": sys.version_info >= (3, 9), "value": platform.python_version(), "required": "3.9+"},
        check_path(CONFIG, "config_json_exists"),
        check_path(EXAMPLE_CONFIG, "config_example_exists"),
        check_path(ROOT / "server.py", "server_py_exists"),
        check_path(ROOT / "windows", "windows_package_exists"),
        check_path(ROOT / "mac" / "OpenDashboard.sh", "mac_launcher_exists"),
    ]
    for filename in REQUIRED_WINDOWS_FILES:
        checks.append(check_path(ROOT / "windows" / filename, f"windows_{filename}"))

    placeholders = config_placeholders(effective)
    checks.append({"label": "config_placeholders_cleared", "ok": not placeholders, "placeholders": placeholders})
    checks.append(can_connect(f"http://127.0.0.1:{port}/api/config", args.timeout) | {"label": "dashboard_api_local"})
    checks.append(can_connect(f"{syncthing_url}/rest/system/ping", args.timeout) | {"label": "syncthing_api_ping"})

    result = {
        "repo": str(ROOT),
        "platform": platform.platform(),
        "local_ip_candidates": local_ip_candidates(),
        "config_path": str(CONFIG),
        "checks": checks,
        "inventory_summary": {
            "adobe_apps": [item.get("name", "") for item in inventory.get("adobe_apps", [])],
            "unity_apps": [item.get("version") or item.get("name", "") for item in inventory.get("unity_apps", [])],
            "font_count": len(inventory.get("fonts", [])),
            "adobe_plugin_count": len(inventory.get("adobe_plugins", [])),
        },
    }
    required_labels = {"python_version", "config_example_exists", "server_py_exists", "windows_package_exists", "mac_launcher_exists"}
    required_labels.update(f"windows_{filename}" for filename in REQUIRED_WINDOWS_FILES)
    result["ok"] = all(item.get("ok") for item in checks if item.get("label") in required_labels)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("SystemSync preflight")
        print("Repo:", result["repo"])
        for item in checks:
            status = "OK" if item.get("ok") else "WARN"
            detail = item.get("value") or item.get("path") or item.get("url") or ""
            if item.get("placeholders"):
                detail = "placeholders: " + ", ".join(item["placeholders"])
            if item.get("error"):
                detail = item["error"]
            print(f"[{status}] {item['label']} {detail}")
        print("Detected Adobe apps:", ", ".join(result["inventory_summary"]["adobe_apps"]) or "none")
        print("Detected Unity editors:", ", ".join(result["inventory_summary"]["unity_apps"]) or "none")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
