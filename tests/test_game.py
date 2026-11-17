#!/usr/bin/env python3
"""Drive ECHOES through a real pseudo-terminal: start, steer, score, pause, die, retry, quit.
Uses pyte (a terminal emulator in Python) to read the screen exactly as a player would see it."""
import os, pty, sys, time, select, termios, struct, fcntl, pyte

PROG = sys.argv[1] if len(sys.argv) > 1 else "./game"
ARGS = sys.argv[2:]
results = []
def check(name, ok, info=""):
    results.append(ok); print(("PASS " if ok else "FAIL ") + name + (f"  ({info})" if info else ""), flush=True)

master, slave = pty.openpty()
fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
before = termios.tcgetattr(slave)
pid = os.fork()
if pid == 0:
    os.setsid(); fcntl.ioctl(slave, termios.TIOCSCTTY, 0)
    for fd in (0, 1, 2): os.dup2(slave, fd)
    os.execv("/bin/sh", ["/bin/sh", "-c", 'exec "$0" "$@"', PROG] + ARGS)
screen = pyte.Screen(80, 24); stream = pyte.ByteStream(screen); raw_log = bytearray()

def pump(t=0.15):
    end = time.time() + t
    while True:
        r, _, _ = select.select([master], [], [], max(0, end - time.time()))
        if not r: break
        try: d = os.read(master, 65536)
        except OSError: break
        if not d: break
        raw_log.extend(d); stream.feed(d)
        if time.time() >= end: break
def key(k, t=0.15): os.write(master, k.encode() if isinstance(k, str) else k); pump(t)
def text(): return "\n".join(screen.display)
def find(ch):
    for y, line in enumerate(screen.display):
        x = line.find(ch)
        if x >= 0: return (x, y)
    return None
def player():
    for y in range(2, 20):
        line = screen.display[y]
        for x in range(1, 77, 2):
            if line[x:x+2] == "██":
                return ((x - 1) // 2, y - 2)
    return None
def gem():
    f = find("◆")
    for y in range(2, 20):
        x = screen.display[y].find("◆")
        if x >= 0: return ((x - 1) // 2, y - 2)
def ghosts():
    s = set()
    for y in range(2, 20):
        line = screen.display[y]
        for x in range(1, 77, 2):
            if line[x:x+2] in ("▒▒", "░░"): s.add(((x - 1) // 2, y - 2))
    return s
def score():
    import re
    m = re.search(r"◆ (\d+)", screen.display[0]); return int(m.group(1)) if m else None

pump(1.0)
check("starts and shows title screen", "ECHOES" in screen.display[0] and "press an arrow key" in text())
open("frame_title.txt", "w").write(text())
check("hides cursor / clears screen", b"\x1b[?25l" in raw_log)
p0 = player(); g0 = gem()
check("player and gem drawn", p0 is not None and g0 is not None, f"player={p0} gem={g0}")

# steer with arrow keys toward gems; greedy bot that avoids ghosts
ESC = {"w": b"\x1b[A", "s": b"\x1b[B", "d": b"\x1b[C", "a": b"\x1b[D"}
D = {"w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0)}
key(ESC["d"], 0.35)
p1 = player()
check("arrow key starts game and moves player", p1 is not None and p0 is not None and p1[0] > p0[0], f"{p0} -> {p1}")
last_dir = "d"; best_seen = 0; frames_with_ghosts = None
t_end = time.time() + 40
while time.time() < t_end and best_seen < 6:
    pump(0.05)
    if "GAME OVER" in text(): break
    p, g = player(), gem()
    if not p or not g: continue
    gh = ghosts()
    opts = []
    for k, (ddx, ddy) in D.items():
        nx, ny = p[0] + ddx, p[1] + ddy
        if not (0 <= nx < 38 and 0 <= ny < 18): continue
        near = sum(1 for (ax, ay) in gh if abs(ax - nx) + abs(ay - ny) <= 1)
        opts.append((near * 100 + abs(g[0] - nx) + abs(g[1] - ny), k))
    if opts:
        opts.sort(); k = opts[0][1]
        if k != last_dir: os.write(master, ESC[k]); last_dir = k
    sc = score() or 0
    if sc > best_seen:
        best_seen = sc
        if sc >= 3 and frames_with_ghosts is None and ghosts():
            frames_with_ghosts = text()
            open("frame_play.txt", "w").write(text())
            raw_frame_at = len(raw_log)
check("collecting gems raises score", best_seen >= 3, f"score reached {best_seen}")
check("each gem leaves a ghost on the board", frames_with_ghosts is not None)

if "GAME OVER" not in text():
    key(" ", 0.3); s1 = text(); key(b"", 0.5); s2 = text()
    died = "GAME OVER" in s1
    check("space pauses (board frozen)", died or ("PAUSED" in s1 and s1.split("\n")[2:20] == s2.split("\n")[2:20]),
          "bot died just before pausing; skipped" if died else ("ok" if "PAUSED" in s1 else "no PAUSED:\n" + s1))
    key(" ", 0.2)
    check("space resumes", "PAUSED" not in text())
    # drive into the top wall
    key(ESC["w"], 0.1)
    for _ in range(40):
        pump(0.1)
        if "GAME OVER" in text(): break
check("hitting a wall/ghost ends the game", "GAME OVER" in text())
open("frame_over.txt", "w").write(text())
key("r", 0.4)
check("r restarts (title screen, score 0)", "press an arrow key" in text() and score() == 0)
key("q", 0.6)
pump(0.5)
try:
    wpid, status = os.waitpid(pid, os.WNOHANG)
except ChildProcessError: wpid, status = pid, 0
check("q quits cleanly", wpid == pid and os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, f"status={status}")
after = termios.tcgetattr(slave)
check("terminal settings restored exactly", before == after)
check("cursor shown again on exit", raw_log.rfind(b"\x1b[?25h") > raw_log.rfind(b"\x1b[?25l"))
check("prints shareable result line", "ECHOES" in text() and "best of" in text(), screen.display[0].strip())
open("frame_share.txt", "w").write(text())
print(f"\n{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
