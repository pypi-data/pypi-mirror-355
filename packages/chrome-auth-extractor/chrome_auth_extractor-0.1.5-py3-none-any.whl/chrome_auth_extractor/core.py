"""
chrome_auth_extractor – core
===========================

Легка бібліотека для отримання авторизаційних даних (cookies + CSRF‑token)
з існуючого профілю Google Chrome. Надає єдину публічну функцію
`get_site_auth(profile, url)` → повертає:

```python
{
    "csrf_token": str | None,
    "cookies": {name: value, ...}
}
```

Ключові принципи
----------------
* запускає **власний headless‑Chrome** і завершує лише його;
* автоматично підбирає вільний порт DevTools;
* шлях профілю може містити пробіли ― передається окремим аргументом;
* мінімум сторонніх пакетів: `requests`, `websocket‑client`.
"""
from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests
import websocket

__all__ = ["get_site_auth"]

# ---------------------------------------------------------------------------
# Константи й допоміжні функції
# ---------------------------------------------------------------------------

CHROME_DEFAULT_PATHS: Tuple[Path, ...] = (
    Path(r"C:/Program Files/Google/Chrome/Application/chrome.exe"),
    Path(r"C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
)


def _find_chrome() -> Path:
    for p in CHROME_DEFAULT_PATHS:
        if p.exists():
            return p
    raise FileNotFoundError(
        "chrome.exe not found – set CHROME_EXE env var or edit CHROME_DEFAULT_PATHS"
    )


def _free_port() -> int:
    """Return an available TCP port (Windows‑safe)."""
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _devtools_json(port: int, timeout: float = 10) -> List[dict]:
    url = f"http://127.0.0.1:{port}/json"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            return requests.get(url, timeout=2).json()
        except requests.RequestException:
            time.sleep(0.4)
    raise RuntimeError("DevTools endpoint did not respond in time")


def _wait_response(ws: websocket.WebSocket, req_id: int) -> dict:
    """Читає WebSocket, поки не прийде відповідь із потрібним id."""
    while True:
        msg = json.loads(ws.recv())
        if msg.get("id") == req_id:
            return msg

# ---------------------------------------------------------------------------
# API‑функція
# ---------------------------------------------------------------------------


def get_site_auth(profile: str | Path, url: str) -> Dict[str, Any]:
    """Зняти cookies і CSRF‑token для сторінки *url* із профілю Chrome *profile*."""

    # 1) Шляхи
    chrome_path = Path(os.getenv("CHROME_EXE", ""))
    if not chrome_path.exists():
        chrome_path = _find_chrome()

    profile_dir = Path(profile)
    if not profile_dir.is_absolute():
        profile_dir = Path(os.environ["LOCALAPPDATA"]) / "Google/Chrome/User Data" / profile_dir
    if not profile_dir.exists():
        raise FileNotFoundError(f"Chrome profile not found: {profile_dir}")

    port = _free_port()

    # 2) Запускаємо headless‑Chrome
    cmd = [
        str(chrome_path),
        f"--remote-debugging-port={port}",
        "--remote-debugging-address=127.0.0.1",
        f"--remote-allow-origins=http://127.0.0.1:{port}",
        "--user-data-dir", str(profile_dir),  # ← окремі елементи, пробіли безпечні
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    browser_ws: websocket.WebSocket | None = None
    try:
        devtools = _devtools_json(port)
        if not devtools:
            raise RuntimeError("DevTools returned empty target list")

        browser_ws = websocket.create_connection(
            devtools[0]["webSocketDebuggerUrl"],
            origin=f"http://127.0.0.1:{port}",
        )

        # ① create about:blank tab
        browser_ws.send(json.dumps({"id": 1, "method": "Target.createTarget", "params": {"url": "about:blank"}}))
        tab_id = _wait_response(browser_ws, 1)["result"]["targetId"]

        # ② attach
        browser_ws.send(json.dumps({"id": 2, "method": "Target.attachToTarget", "params": {"targetId": tab_id, "flatten": True}}))
        session_id = _wait_response(browser_ws, 2)["result"]["sessionId"]

        def _send(mid: int, method: str, params: dict | None = None) -> dict:
            browser_ws.send(json.dumps({
                "sessionId": session_id,
                "id": mid,
                "method": method,
                "params": params or {},
            }))
            return _wait_response(browser_ws, mid)

        # ③ enable domains & navigate
        _send(3, "Network.enable")
        _send(4, "Page.enable")
        _send(5, "Page.navigate", {"url": url})
        time.sleep(2)  # у більш суворому варіанті – чекати Page.loadEventFired

        # ④ cookies
        cookie_objs = _send(6, "Network.getCookies", {"urls": [url]})["result"]["cookies"]
        cookies = {c["name"]: c["value"] for c in cookie_objs}

        # ⑤ CSRF token
        js = "document.querySelector('meta[name=\"csrf-token\"]')?.content || ''"
        eval_res = _send(7, "Runtime.evaluate", {"expression": js, "returnByValue": True})
        csrf_token = eval_res["result"]["result"].get("value") or None

        return {"csrf_token": csrf_token, "cookies": cookies}

    finally:
        if browser_ws is not None:
            try:
                browser_ws.close()
            except Exception:
                pass
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(3)
        except subprocess.TimeoutExpired:
            proc.kill()
