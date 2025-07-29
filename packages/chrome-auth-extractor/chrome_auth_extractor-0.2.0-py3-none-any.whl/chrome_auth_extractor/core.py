"""
chrome_auth_extractor – core
============================
Знімає cookies + CSRF-token із заданого профілю Chrome у headless-режимі.
"""

from __future__ import annotations
import json, os, signal, socket, subprocess, time, getpass, traceback, contextlib
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests, websocket

__all__ = ["get_site_auth"]

# ─── Параметри ─────────────────────────────────────────────────────
DEBUG = False               # True → показує повну команду і середовище
WAIT_LOAD_SEC = 2           # sleep перед читанням DOM
# ──────────────────────────────────────────────────────────────────

CHROME_DEFAULT_PATHS: Tuple[Path, ...] = (
    Path(r"C:/Program Files/Google/Chrome/Application/chrome.exe"),
    Path(r"C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
)


def _is_chrome_file(p: Path) -> bool:
    return p.is_file() and p.name.lower() == "chrome.exe"


def _find_chrome() -> Path:
    for p in CHROME_DEFAULT_PATHS:
        if _is_chrome_file(p):
            return p
    raise FileNotFoundError(
        "chrome.exe not found – set CHROME_EXE env var or edit CHROME_DEFAULT_PATHS"
    )


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _devtools_json(port: int, timeout=10) -> List[dict]:
    url = f"http://127.0.0.1:{port}/json"
    end = time.time() + timeout
    while time.time() < end:
        try:
            return requests.get(url, timeout=2).json()
        except requests.RequestException:
            time.sleep(0.4)
    raise RuntimeError("DevTools endpoint did not respond")


def _wait(ws: websocket.WebSocket, req_id: int) -> dict:
    while True:
        msg = json.loads(ws.recv())
        if msg.get("id") == req_id:
            return msg


# ─── API ───────────────────────────────────────────────────────────


def get_site_auth(profile: str | Path, url: str) -> Dict[str, Any]:
    # 1. chrome.exe
    env_path = os.getenv("CHROME_EXE", "").strip('"')
    chrome_path = Path(env_path)
    if not _is_chrome_file(chrome_path):
        chrome_path = _find_chrome()

    # 2. профіль
    prof_dir = Path(profile)
    if not prof_dir.is_absolute():
        prof_dir = (
            Path(os.environ["LOCALAPPDATA"])
            / "Google/Chrome/User Data"
            / prof_dir
        )
    if not prof_dir.exists():
        raise FileNotFoundError(f"Chrome profile not found: {prof_dir}")

    port = _free_port()

    cmd = [
        str(chrome_path),
        f"--remote-debugging-port={port}",
        "--remote-debugging-address=127.0.0.1",
        f"--remote-allow-origins=http://127.0.0.1:{port}",
        "--user-data-dir",
        str(prof_dir),
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
    ]

    if DEBUG:
        from ctypes import windll

        print("\n=== chrome_auth_extractor DEBUG ===")
        print("User        :", getpass.getuser())
        print("IsAdmin     :", bool(windll.shell32.IsUserAnAdmin()))
        print("Chrome exe  :", chrome_path)
        print("Profile dir :", prof_dir)
        print("DevTools    :", port)
        print("Command     :", subprocess.list2cmdline(cmd))
        print("===================================\n")

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except PermissionError as e:
        raise PermissionError(
            "WinError 5 while launching Chrome.\n"
            "Перевірте ACL профілю та чи дозволено запуск Chrome із прапорцями headless."
        ) from e

    ws: websocket.WebSocket | None = None
    try:
        targets = _devtools_json(port)
        ws = websocket.create_connection(
            targets[0]["webSocketDebuggerUrl"],
            origin=f"http://127.0.0.1:{port}",
        )

        # create tab + attach
        ws.send(json.dumps({"id": 1, "method": "Target.createTarget", "params": {"url": "about:blank"}}))
        tab_id = _wait(ws, 1)["result"]["targetId"]
        ws.send(json.dumps({"id": 2, "method": "Target.attachToTarget", "params": {"targetId": tab_id, "flatten": True}}))
        sess = _wait(ws, 2)["result"]["sessionId"]

        def send(mid: int, method: str, params: dict | None = None) -> dict:
            ws.send(json.dumps({"sessionId": sess, "id": mid, "method": method, "params": params or {}}))
            return _wait(ws, mid)

        send(3, "Network.enable")
        send(4, "Page.enable")
        send(5, "Page.navigate", {"url": url})
        time.sleep(WAIT_LOAD_SEC)

        cookies = {
            c["name"]: c["value"]
            for c in send(6, "Network.getCookies", {"urls": [url]})["result"]["cookies"]
        }

        js = "document.querySelector('meta[name=\"csrf-token\"]')?.content || ''"
        csrf = send(7, "Runtime.evaluate", {"expression": js, "returnByValue": True})[
            "result"
        ]["result"].get("value") or None

        return {"csrf_token": csrf, "cookies": cookies}

    finally:
        if ws:
            with contextlib.suppress(Exception):
                ws.close()
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(3)
        except subprocess.TimeoutExpired:
            proc.kill()
