"""Dev tool: run the page in headless Edge emulating a phone (touch, mobile
viewport) and drive it with real CDP touch events; take screenshots.

    python ports/wasm/touch_test.py <url> <out dir> --size 390x844 [--steps "..."] [--gpu]

Steps (comma separated, run in order):
  w:S               wait S seconds
  shot              screenshot -> shot_<k>.png
  tap:LABEL[:S]     touch the #tc button whose text starts with LABEL for S seconds (default 0.15)
  hold:LABEL        touch LABEL and keep holding (released by 'up:LABEL')
  up:LABEL          release a held button
  stick:DX:DY:S     drag the stick from its home by (DX, DY) * radius for S seconds
  js:EXPR           evaluate EXPR in the page and print the result
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


class Page:
    def __init__(self, ws):
        self.ws, self.n, self.console = ws, 0, []

    def call(self, method, **params):
        self.n += 1
        mid = self.n
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params}))
        while True:
            m = json.loads(self.ws.recv())
            if m.get("method") == "Runtime.consoleAPICalled":
                self.console.append(" ".join(str(a.get("value", a.get("description", ""))) for a in m["params"].get("args", [])))
            if m.get("id") == mid:
                return m.get("result", {})

    def pump(self, secs):
        t = time.time() + secs
        self.ws.settimeout(0.2)
        while time.time() < t:
            try:
                m = json.loads(self.ws.recv())
                if m.get("method") == "Runtime.consoleAPICalled":
                    self.console.append(" ".join(str(a.get("value", "")) for a in m["params"].get("args", [])))
            except websocket.WebSocketTimeoutException:
                pass
        self.ws.settimeout(240)

    def js(self, expr):
        r = self.call("Runtime.evaluate", expression=expr, returnByValue=True)
        return r.get("result", {}).get("value")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("out")
    ap.add_argument("--size", default="390x844")
    ap.add_argument("--steps", default="w:10,shot")
    ap.add_argument("--gpu", action="store_true", help="hardware GPU (default SwiftShader)")
    ap.add_argument("--port", type=int, default=9335)
    a = ap.parse_args()
    W, H = (int(v) for v in a.size.split("x"))
    os.makedirs(a.out, exist_ok=True)
    prof = tempfile.mkdtemp(prefix="touch_")
    args = [EDGE, "--headless=new", f"--user-data-dir={prof}", f"--remote-debugging-port={a.port}",
            "--remote-allow-origins=*", "--no-first-run", "--autoplay-policy=no-user-gesture-required",
            f"--window-size={W},{H}", "--touch-events=enabled"]
    if not a.gpu:
        args += ["--enable-unsafe-swiftshader", "--use-angle=swiftshader", "--ignore-gpu-blocklist"]
    p = subprocess.Popen(args + ["about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shots = 0
    try:
        for _ in range(50):
            try:
                tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{a.port}/json"))
                break
            except OSError:
                time.sleep(0.2)
        tab = next(t for t in tabs if t.get("type") == "page")
        pg = Page(websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=240))
        pg.call("Runtime.enable")
        pg.call("Emulation.setDeviceMetricsOverride", width=W, height=H, deviceScaleFactor=2, mobile=True)
        pg.call("Emulation.setTouchEmulationEnabled", enabled=True, maxTouchPoints=5)
        pg.call("Emulation.setEmitTouchEventsForMouse", enabled=True)
        pg.call("Page.enable")
        pg.call("Page.navigate", url=a.url)
        held = {}                        # touch id -> (x, y)
        labels = {}                      # held button label -> touch id
        next_id = [1]

        def center(label):
            return pg.js("""(function(){var b=[].slice.call(document.querySelectorAll('#tc .btn')).find(function(e){
                return e.textContent.trim().toUpperCase().indexOf(%s)===0});if(!b)return null;var r=b.getBoundingClientRect();
                return [r.left+r.width/2,r.top+r.height/2]})()""" % json.dumps(label.upper()))

        def touch(kind):
            pts = [{"x": x, "y": y, "id": i} for i, (x, y) in held.items()]
            pg.call("Input.dispatchTouchEvent", type=kind, touchPoints=pts)

        for step in a.steps.split(","):
            print("step", step, flush=True)
            parts = step.split(":")
            op = parts[0]
            if op == "w":
                pg.pump(float(parts[1]))
            elif op == "shot":
                r = pg.call("Page.captureScreenshot", format="png")
                open(os.path.join(a.out, f"shot_{shots}.png"), "wb").write(base64.b64decode(r["data"]))
                shots += 1
            elif op in ("tap", "hold"):
                c = center(parts[1])
                if not c:
                    print("no button", parts[1])
                    continue
                i = next_id[0]; next_id[0] += 1
                held[i] = tuple(c)
                touch("touchStart")
                if op == "tap":
                    pg.pump(float(parts[2]) if len(parts) > 2 else 0.15)
                    x, y = held.pop(i)
                    pg.call("Input.dispatchTouchEvent", type="touchEnd", touchPoints=[{"x": x, "y": y, "id": i}])
                else:
                    labels[parts[1]] = i
            elif op == "up":
                i = labels.pop(parts[1], None)
                if i is not None:
                    x, y = held.pop(i)
                    pg.call("Input.dispatchTouchEvent", type="touchEnd", touchPoints=[{"x": x, "y": y, "id": i}])
            elif op in ("stick", "stickhold"):
                home = pg.js("(function(){var b=document.querySelector('#tc .base');var r=b.getBoundingClientRect();"
                             "return [r.left+r.width/2,r.top+r.height/2,r.width/2]})()")
                dx, dy, secs = float(parts[1]), float(parts[2]), float(parts[3])
                i = next_id[0]; next_id[0] += 1
                held[i] = (home[0], home[1])
                touch("touchStart")
                for k in range(1, 6):
                    held[i] = (home[0] + dx * home[2] * k / 5, home[1] + dy * home[2] * k / 5)
                    touch("touchMove")
                    pg.pump(0.03)
                pg.pump(secs)
                if op == "stickhold":
                    labels["STICK"] = i
                    continue
                x, y = held.pop(i)
                pg.call("Input.dispatchTouchEvent", type="touchEnd", touchPoints=[{"x": x, "y": y, "id": i}])
            elif op == "js":
                print("js:", pg.js(step[3:]))
    finally:
        p.kill()
        time.sleep(0.5)
        shutil.rmtree(prof, ignore_errors=True)
    open(os.path.join(a.out, "console.txt"), "w", encoding="utf-8").write("\n".join(pg.console))
    print(f"{shots} screenshots, {len(pg.console)} console lines -> {a.out}")


if __name__ == "__main__":
    main()
