"""
chrome_auth_extractor
---------------------

Легка бібліотека для отримання авторизаційних даних (куки + CSRF-token)
з профілю Google Chrome у headless‑режимі.

Основна функція:
    get_site_auth(profile: str | Path, url: str) -> dict

Повертає словник:
    {
        "csrf_token": str | None,
        "cookies": dict[str, str]   # name -> value
    }

Бібліотека працює обережно:
  • НЕ завершує довільні вікна Chrome – лише власний headless‑процес.
  • Вибирає вільний порт для DevTools, щоб уникнути конфліктів.

Залежності: requests, websocket-client (pip install chrome-auth-extractor[full]).
"""

from __future__ import annotations

__all__ = [
    "get_site_auth",
]

import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests
import websocket

# ---- Константи -------------------------------------------------------------

CHROME_DEFAULT_PATHS: Tuple[Path, ...] = (
    Path(r"C:/Program Files/Google/Chrome/Application/chrome.exe"),
    Path(r"C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
)

# ---------------------------------------------------------------------------
# Внутрішні утиліти
# ---------------------------------------------------------------------------

def _find_chrome() -> Path:
    for p in CHROME_DEFAULT_PATHS:
        if p.exists():
            return p
    raise FileNotFoundError(
        "chrome.exe not found – specify CHROME_EXE environment variable or add path to CHROME_DEFAULT_PATHS"
    )

def _free_port() -> int:
    """Знаходимо вільний TCP‑порт (Windows‑safe)."""
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]

def _devtools_json(port: int, timeout: float = 10) -> List[dict]:
    url = f"http://127.0.0.1:{port}/json"
    end = time.time() + timeout
    while time.time() < end:
        try:
            return requests.get(url, timeout=2).json()
        except requests.RequestException:
            time.sleep(0.4)
    raise RuntimeError("DevTools endpoint did not respond within timeout")

def _wait_response(ws: websocket.WebSocket, req_id: int) -> dict:
    while True:
        msg = json.loads(ws.recv())
        if msg.get("id") == req_id:
            return msg

# ---------------------------------------------------------------------------
# Головна публічна функція
# ---------------------------------------------------------------------------

def get_site_auth(profile: str | Path, url: str) -> Dict[str, Any]:
    """Отримати cookies + CSRF‑token для заданого профілю Chrome і URL.

    Parameters
    ----------
    profile : str | pathlib.Path
        Ім'я папки профілю ("Profile 1") **або** абсолютний шлях до папки
        (наприклад, ``%LOCALAPPDATA%/Google/Chrome/User Data/Profile 1``).
    url : str
        Повний URL сайту, для якого потрібні дані (наприклад,
        "https://mangabuff.ru/").

    Returns
    -------
    dict
        ``{"csrf_token": str | None, "cookies": {name: value, ...}}``
    """

    # --- Локальні налаштування
    chrome_path = Path(os.getenv("CHROME_EXE", ""))
    if not chrome_path.exists():
        chrome_path = _find_chrome()

    profile_dir = Path(profile)
    if not profile_dir.is_absolute():
        profile_dir = (
            Path(os.environ["LOCALAPPDATA"]) / "Google/Chrome/User Data" / profile_dir
        )
    if not profile_dir.exists():
        raise FileNotFoundError(f"Chrome profile not found: {profile_dir}")

    port = _free_port()

    # --- Запуск headless‑Chrome
    cmd = [
        str(chrome_path),
        f"--remote-debugging-port={port}",
        "--remote-debugging-address=127.0.0.1",
        f"--remote-allow-origins=http://127.0.0.1:{port}",
        f'--user-data-dir="{profile_dir}"',
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        devtools = _devtools_json(port)
        if not devtools:
            raise RuntimeError("DevTools returned empty list")
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

        def ssend(mid: int, method: str, params: dict | None = None) -> dict:
            browser_ws.send(json.dumps({
                "sessionId": session_id,
                "id": mid,
                "method": method,
                "params": params or {},
            }))
            return _wait_response(browser_ws, mid)

        # ③ enable domains & navigate
        ssend(3, "Network.enable")
        ssend(4, "Page.enable")
        ssend(5, "Page.navigate", {"url": url})
        time.sleep(2)  # дочекатись завантаження (можна замінити на Page.loadEventFired)

        # ④ cookies for URL
        cookie_objs = ssend(6, "Network.getCookies", {"urls": [url]})["result"]["cookies"]
        cookies = {c["name"]: c["value"] for c in cookie_objs}

        # ⑤ CSRF token
        js = "document.querySelector('meta[name=\"csrf-token\"]')?.content || ''"
        result_obj = ssend(7, "Runtime.evaluate", {"expression": js, "returnByValue": True})
        csrf_token = result_obj["result"]["result"].get("value") or None

        return {"csrf_token": csrf_token, "cookies": cookies}

    finally:
        browser_ws.close()
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(3)
        except subprocess.TimeoutExpired:
            proc.kill()
