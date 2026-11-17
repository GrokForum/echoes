#!/usr/bin/env python3
"""Play ECHOES with a simple bot in a pseudo-terminal and save a mid-game frame as preview.png."""
import os, pty, time, select, termios, struct, fcntl, pyte, re, copy
from PIL import Image, ImageDraw, ImageFont
master, slave = pty.openpty()
fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
pid = os.fork()
if pid == 0:
    os.setsid(); fcntl.ioctl(slave, termios.TIOCSCTTY, 0)
    for fd in (0, 1, 2): os.dup2(slave, fd)
    os.execv("./echoes.elf", ["./echoes.elf"])
scr = pyte.Screen(80, 24); st = pyte.ByteStream(scr)
def pump(t):
    end = time.time() + t
    while time.time() < end:
        r, _, _ = select.select([master], [], [], max(0, end - time.time()))
        if r: st.feed(os.read(master, 65536))
def cells(chs):
    out = set()
    for y in range(2, 20):
        line = scr.display[y]
        for x in range(1, 77, 2):
            if line[x:x+2] in chs: out.add(((x - 1) // 2, y - 2))
    return out
ESC = {"w": b"\x1b[A", "s": b"\x1b[B", "d": b"\x1b[C", "a": b"\x1b[D"}
D = {"w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0)}
pump(0.6); os.write(master, ESC["d"]); last = "d"; snap = None; best = 0
t_end = time.time() + 120
while time.time() < t_end:
    pump(0.04)
    txt = "\n".join(scr.display)
    m = re.search(r"◆ (\d+)", scr.display[0]); s = int(m.group(1)) if m else 0
    if "GAME OVER" in txt:
        os.write(master, b"r"); pump(0.3); os.write(master, ESC["d"]); last = "d"; continue
    p = cells({"██"}); g = None
    for y in range(2, 20):
        x = scr.display[y].find("◆")
        if x >= 0: g = ((x - 1) // 2, y - 2)
    if not p or not g: continue
    p = next(iter(p)); gh = cells({"▒▒", "░░"})
    opts = []
    for k, (dx, dy) in D.items():
        nx, ny = p[0] + dx, p[1] + dy
        if not (0 <= nx < 38 and 0 <= ny < 18): continue
        danger = sum(1 for (ax, ay) in gh if abs(ax - nx) + abs(ay - ny) <= 2)
        opts.append((danger * 100 + abs(g[0] - nx) + abs(g[1] - ny), k))
    opts.sort(); k = opts[0][1]
    if k != last: os.write(master, ESC[k]); last = k
    if s >= 10 and len(cells({"· "})) >= 3 and snap is None:
        snap = copy.deepcopy(scr.buffer); break
    best = max(best, s)
os.write(master, b"q"); pump(0.3); os.waitpid(pid, 0)
assert snap, f"bot never reached 10 (best {best})"
# render
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 18)
bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 18)
CW, CH = 11, 22
named = {"default": (200, 200, 200), "black": (0, 0, 0), "red": (205, 49, 49), "green": (13, 188, 121), "brown": (229, 229, 16),
         "yellow": (229, 229, 16), "blue": (36, 114, 200), "magenta": (188, 63, 188), "cyan": (17, 168, 205), "white": (229, 229, 229),
         "brightblack": (102, 102, 102), "brightred": (241, 76, 76), "brightgreen": (35, 209, 139), "brightyellow": (245, 245, 67), "brightbrown": (245, 245, 67),
         "brightblue": (59, 142, 234), "brightmagenta": (214, 112, 214), "brightcyan": (41, 184, 219), "brightwhite": (255, 255, 255)}
def col(c, b):
    if re.fullmatch(r"[0-9a-fA-F]{6}", c): return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
    if b and c in ("white", "default"): return named["brightwhite"]
    return named.get(c, named["default"])
img = Image.new("RGB", (80 * CW + 20, 22 * CH + 20), (16, 16, 20)); dr = ImageDraw.Draw(img)
for y in range(22):
    for x in range(80):
        ch = snap[y][x]
        if ch.data.strip():
            dr.text((10 + x * CW, 10 + y * CH), ch.data, font=bold if ch.bold else font, fill=col(ch.fg, ch.bold))
img.save("preview.png"); print("preview.png saved; frame score >= 10")
open("frame_preview.txt", "w").write("\n".join("".join(snap[y][x].data for x in range(80)) for y in range(22)))
