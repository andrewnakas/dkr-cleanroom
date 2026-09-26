"""Dev tool: open a page in headless Edge and take real screenshots over CDP
(Page.captureScreenshot) at given seconds. Unlike headless_shot.py this does
not route PNGs through the console log, so long runs stay reliable.

    python ports/wasm/cdp_shot.py <url> <out dir> --secs 60,80 [--webgl] [--port 9334]

Writes shot_<k>.png and console.txt (page console lines).
"""
import argparse
import base64
import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.request

import websocket

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("out")
    ap.add_argument("--secs", default="10")
    ap.add_argument("--webgl", action="store_true")
    ap.add_argument("--port", type=int, default=9334)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    secs = sorted(float(s) for s in a.secs.split(","))
    prof = tempfile.mkdtemp(prefix="cdpshot_")
    args = [EDGE, "--headless=new", f"--user-data-dir={prof}", f"--remote-debugging-port={a.port}",
            "--remote-allow-origins=*", "--no-first-run", "--autoplay-policy=no-user-gesture-required",
            "--window-size=660,500"]
    if a.webgl:
        args += ["--enable-unsafe-swiftshader", "--use-angle=swiftshader", "--ignore-gpu-blocklist"]
    p = subprocess.Popen(args + ["about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    lines = []
    try:
        for _ in range(50):
            try:
                tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{a.port}/json"))
                break
            except OSError:
                time.sleep(0.2)
        tab = next(t for t in tabs if t.get("type") == "page")
        ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=30)
        n = [0]

        def send(method, **params):
            n[0] += 1
            ws.send(json.dumps({"id": n[0], "method": method, "params": params}))
            return n[0]

        send("Runtime.enable")
        send("Page.enable")
        t0 = time.time()
        send("Page.navigate", url=a.url)
        ws.settimeout(0.5)
        pending = {}
        k = 0
        while k < len(secs) or pending:
            if k < len(secs) and time.time() - t0 >= secs[k]:
                pending[send("Page.captureScreenshot", format="png")] = k
                k += 1
            try:
                m = json.loads(ws.recv())
            except websocket.WebSocketTimeoutException:
                if time.time() - t0 > secs[-1] + 60:
                    break
                continue
            if m.get("method") == "Runtime.consoleAPICalled":
                args_ = m["params"].get("args", [])
                lines.append(" ".join(str(x.get("value", x.get("description", ""))) for x in args_))
            if m.get("id") in pending:
                i = pending.pop(m["id"])
                data = m.get("result", {}).get("data")
                if data:
                    open(os.path.join(a.out, f"shot_{i}.png"), "wb").write(base64.b64decode(data))
    finally:
        p.kill()
        time.sleep(0.5)
        shutil.rmtree(prof, ignore_errors=True)
    open(os.path.join(a.out, "console.txt"), "w", encoding="utf-8").write("\n".join(lines))
    shots = sorted(f for f in os.listdir(a.out) if f.startswith("shot_"))
    print(f"{len(shots)} screenshots, {len(lines)} console lines -> {a.out}")


if __name__ == "__main__":
    main()
