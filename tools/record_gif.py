#!/usr/bin/env python3
"""Record real ECHOES gameplay as an asciicast v2 file (a simple bot steers), then render it with agg:
    python3 tools/record_gif.py assets/echoes.cast && agg --font-size 16 assets/echoes.cast assets/echoes.gif
Every frame in the recording is the game's own terminal output; nothing is drawn by hand."""
import os, pty, time, select, termios, struct, fcntl, json, sys, re, pyte
out = sys.argv[1] if len(sys.argv) > 1 else "echoes.cast"
W, H = 80, 24
master, slave = pty.openpty()
fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", H, W, 0, 0))
pid = os.fork()
if pid == 0:
    os.setsid(); fcntl.ioctl(slave, termios.TIOCSCTTY, 0)
    for fd in (0, 1, 2): os.dup2(slave, fd)
    os.environ["TERM"] = "xterm-256color"
    os.execv("/bin/sh", ["/bin/sh", "-c", "./game"])
scr = pyte.Screen(W, H); st = pyte.ByteStream(scr)
t0 = time.time(); events = []; dec = __import__("codecs").getincrementaldecoder("utf-8")("replace")
def pump(t):
    end = time.time() + t
    while time.time() < end:
        r, _, _ = select.select([master], [], [], max(0, end - time.time()))
        if r:
            try: d = os.read(master, 65536)
            except OSError: return
            st.feed(d); s = dec.decode(d)
            if s: events.append([round(time.time() - t0, 4), "o", s])
def cells(chs):
    o = set()
    for y in range(2, 20):
        line = scr.display[y]
        for x in range(1, 77, 2):
            if line[x:x+2] in chs: o.add(((x - 1) // 2, y - 2))
    return o
ESC = {"w": b"\x1b[A", "s": b"\x1b[B", "d": b"\x1b[C", "a": b"\x1b[D"}
D = {"w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0)}
pump(1.5)                                   # title screen
os.write(master, ESC["d"]); last = "d"
t_end = time.time() + 40
while time.time() < t_end:
    pump(0.04)
    if "GAME OVER" in "\n".join(scr.display): break
    m = re.search(r"◆ (\d+)", scr.display[0]); s = int(m.group(1)) if m else 0
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
    if s >= 12: opts.sort(reverse=True)    # after 12 gems, steer into trouble so the clip ends
    else: opts.sort()
    k = opts[0][1]
    if k != last: os.write(master, ESC[k]); last = k
pump(2.5)                                   # game-over screen
os.write(master, b"q"); pump(3.0)           # share line
try: os.waitpid(pid, 0)
except ChildProcessError: pass
events.append([round(time.time() - t0, 4), "o", ""])
with open(out, "w") as f:
    f.write(json.dumps({"version": 2, "width": W, "height": H, "title": "ECHOES (3,771 bytes)"}) + "\n")
    for e in events: f.write(json.dumps(e) + "\n")
print(f"{out}: {len(events)} events, {events[-1][0]:.1f}s")
