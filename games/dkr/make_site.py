"""Package a built tree into a static site. Usage: python -m games.dkr.make_site <tree> <site dir>"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

ABOUT = ("Diddy Kong Racing built from the community decompilation and its PC port, for the browser. "
         "Every texture, font, sprite and sound the decomp normally extracts from a ROM was regenerated "
         "(clean room); no ROM is needed or used. Saves stay in this browser.")
CONTROLS = ("<kbd>Arrows</kbd>/<kbd>WASD</kbd> steer &middot; <kbd>X</kbd> A (accelerate) &middot; "
            "<kbd>C</kbd> B (brake) &middot; <kbd>Z</kbd> Z (item) &middot; <kbd>Space</kbd>/<kbd>Shift</kbd> R (hop) &middot; "
            "<kbd>Q</kbd> L &middot; <kbd>Enter</kbd> Start &middot; <kbd>I J K L</kbd> C buttons &middot; gamepads work too &middot; on phones: touch stick and buttons, optional Auto-gas")


def main(tree, site):
    b = os.path.join(tree, "build", "web")
    os.makedirs(site, exist_ok=True)
    for f in ("dkr.js", "dkr.wasm", "dkr.data"):
        shutil.copy(os.path.join(b, f), os.path.join(site, f))
    html = open(os.path.join(ROOT, "ports", "web", "shell.html"), encoding="utf-8").read()
    html = html.split("\n", 1)[1]  # drop the template comment
    html = (html.replace("{{TITLE}}", "Diddy Kong Racing (clean room)").replace("{{ABOUT}}", ABOUT)
            .replace("{{CONTROLS}}", CONTROLS).replace("{{SCRIPT}}", "dkr.js"))
    # dev hook (inactive unless ?script= is given): see web/devscript.js
    # touch overlay for phones/tablets: web/touchpad.js
    for js in ("devscript.js", "touchpad.js"):
        shutil.copy(os.path.join(HERE, "web", js), os.path.join(site, js))
    html = html.replace("</body>", '<script src="touchpad.js"></script>\n<script src="devscript.js"></script>\n</body>')
    html = html.replace('<meta name="viewport" content="width=device-width, initial-scale=1">',
                        '<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, '
                        'user-scalable=no, viewport-fit=cover">\n<meta name="apple-mobile-web-app-capable" content="yes">\n'
                        '<meta name="mobile-web-app-capable" content="yes">')
    open(os.path.join(site, "index.html"), "w", encoding="utf-8", newline="\n").write(html)
    open(os.path.join(site, ".nojekyll"), "w").close()
    for f in sorted(os.listdir(site)):
        print(os.path.getsize(os.path.join(site, f)), f)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
