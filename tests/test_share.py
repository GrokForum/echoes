#!/usr/bin/env python3
"""Score, share card, and pause. Drives the real binary through a pty.

The share text and the fuse bar are read back from the terminal. This file does not
reimplement the grade formula; a grab taken on a full bar must come out fast (green)
and a grab taken on a nearly empty bar must come out slow (orange), in that order.
"""
import os, pty, re, sys, time, select, termios, struct, fcntl, pyte
from collections import deque

PROG = sys.argv[1] if len(sys.argv) > 1 else "./echoes.elf"
results = []

def check(name, ok, info=""):
    results.append(ok)
    print(("PASS " if ok else "FAIL ") + name + (f"  ({info})" if info else ""), flush=True)

class Run:
    def __init__(self, argv):
        self.master, self.slave = pty.openpty()
        fcntl.ioctl(self.slave, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
        self.before = termios.tcgetattr(self.slave)
        self.pid = os.fork()
        if self.pid == 0:
            os.setsid()
            fcntl.ioctl(self.slave, termios.TIOCSCTTY, 0)
            for fd in (0, 1, 2):
                os.dup2(self.slave, fd)
            os.execv(argv[0], argv)
        self.screen = pyte.Screen(80, 24)
        self.stream = pyte.ByteStream(self.screen)
        self.log = bytearray()
        self.heading = None

    def pump(self, t):
        end = time.time() + t
        while time.time() < end:
            r, _, _ = select.select([self.master], [], [], max(0, end - time.time()))
            if not r:
                continue
            try:
                d = os.read(self.master, 65536)
            except OSError:
                break
            if not d:
                break
            self.log.extend(d)
            self.stream.feed(d)

    def key(self, k, t=0.02):
        os.write(self.master, k if isinstance(k, bytes) else k.encode())
        self.pump(t)

    def text(self):
        return "\n".join(self.screen.display)

    def over(self):
        return "GAME OVER" in self.text()

    def alive(self):
        w, _ = os.waitpid(self.pid, os.WNOHANG)
        return w == 0

    def player(self):
        for y in range(2, 20):
            line = self.screen.display[y]
            for x in range(1, 77, 2):
                if line[x:x + 2] == "██":
                    return ((x - 1) // 2, y - 2)
        return None

    def gem_at(self):
        # The HUD diamond is on row 0. A board gem is a later row.
        # The pause label is painted over the middle of the board, so callers
        # that need the gem while paused must have saved it beforehand.
        for y in range(2, 20):
            x = self.screen.display[y].find("◆")
            if x >= 0:
                return ((x - 1) // 2, y - 2)
        return None

    def ghosts(self):
        s = set()
        for y in range(2, 20):
            line = self.screen.display[y]
            for x in range(1, 77, 2):
                if line[x:x + 2] in ("▒▒", "░░"):
                    s.add(((x - 1) // 2, y - 2))
        return s

    def score(self):
        m = re.search(r"◆ (\d+)", self.screen.display[0])
        return int(m.group(1)) if m else None

    def best(self):
        m = re.search(r"best (\d+)", self.screen.display[0])
        return int(m.group(1)) if m else None

    def fuse(self):
        return self.screen.display[0].count("█")

    def quit(self):
        self.key(b"q", 0.4)

    def restored(self):
        return termios.tcgetattr(self.slave) == self.before

ARROW = {"w": b"\x1b[A", "s": b"\x1b[B", "a": b"\x1b[D", "d": b"\x1b[C"}
DELTA = {"w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0)}

def bfs(start, goal, blocked):
    if start == goal:
        return []
    q = deque([start])
    prev = {start: None}
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if not (0 <= n[0] < 38 and 0 <= n[1] < 18) or n in blocked or n in prev:
                continue
            prev[n] = (x, y)
            if n == goal:
                path = [n]
                while prev[path[-1]] != start:
                    path.append(prev[path[-1]])
                path.reverse()
                return path
            q.append(n)
    return None

def dir_of(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    if dx == 1: return "d"
    if dx == -1: return "a"
    if dy == 1: return "s"
    return "w"

def one_cell(r, k):
    prev = r.player()
    if r.heading != k:
        r.key(ARROW[k])
        r.heading = k
    end = time.time() + 0.45
    while time.time() < end:
        r.pump(0.03)
        if r.over():
            return None
        p = r.player()
        if p and p != prev:
            return p
    return r.player()

def toward(r, dest, blocked, limit=90):
    for _ in range(limit):
        if r.over():
            return False
        p = r.player()
        if p == dest:
            return True
        if p is None:
            r.pump(0.05)
            continue
        path = bfs(p, dest, blocked())
        if not path:
            return False
        if one_cell(r, dir_of(p, path[0])) is None:
            return False
    return r.player() == dest

def share_of(log):
    s = log.decode("utf-8", "replace")
    i = s.rfind("best of")
    if i < 0:
        return None
    j = s.rfind("ECHOES", 0, i)
    block = s[j:]
    m = re.search(r"ECHOES (?:#(\d+)|practice) ▸ (\d+) gems, best of (\d+) tr", block)
    squares = re.findall("[🟩🟨🟧]", block)
    return m, squares, block

def on_board(cell):
    return 0 <= cell[0] < 38 and 0 <= cell[1] < 18

def on_rim(cell):
    return cell[0] in (0, 37) or cell[1] in (0, 17)

def escape_dir(cell, facing, avoid):
    """Leave `cell` on a heading whose next two steps stay on the board.

    The snake keeps its heading for the tick after the turn, so a one-cell
    escape onto the rim walks off the board before a pause can land.
    Prefer a cell off the patrol and off the rim.
    """
    best = None
    for ek, (dx, dy) in DELTA.items():
        if ek == facing:
            continue
        n = (cell[0] + dx, cell[1] + dy)
        n2 = (n[0] + dx, n[1] + dy)
        if not on_board(n) or not on_board(n2):
            continue
        rank = (n in avoid, on_rim(n), n2 in avoid, on_rim(n2), ek)
        if best is None or rank < best[0]:
            best = (rank, ek)
    if best:
        return best[1]
    for ek, (dx, dy) in DELTA.items():
        if ek != facing and on_board((cell[0] + dx, cell[1] + dy)):
            return ek
    return facing

def grab_one(r, route):
    """Take the gem that is on screen. Queue the step off that cell before entering it,
    so a slow test cannot lose the race and walk off the board on the next tick."""
    for _ in range(90):
        if r.over():
            return None
        if r.score() == 1:
            held = r.gem_at()
            r.key(b" ")
            r.pump(0.3)
            if r.player():
                route.add(r.player())
            return held
        p, g = r.player(), r.gem_at()
        if p:
            route.add(p)
        if not p or not g:
            r.pump(0.05)
            continue
        path = bfs(p, g, set())
        if not path:
            return None
        if len(path) == 1 and r.heading == dir_of(p, g):
            # Already facing the gem. Step aside so the grab and the escape can be queued together.
            aside = escape_dir(p, r.heading, route)
            one_cell(r, aside)
            continue
        if len(path) <= 2:
            route.add(g)  # the ghost will patrol this cell
            k_grab = dir_of(path[-2], g) if len(path) == 2 else dir_of(p, g)
            k_esc = escape_dir(g, k_grab, route)
            keys = b""
            if len(path) == 2:
                keys += ARROW[dir_of(p, path[0])]
            keys += ARROW[k_grab] + ARROW[k_esc]
            os.write(r.master, keys)
            r.heading = k_esc
            end = time.time() + 1.5
            while time.time() < end and not r.over():
                r.pump(0.02)
                # Read the new gem before the pause label can cover it.
                if r.score() == 1 and r.player() and r.player() != g:
                    held = r.gem_at()
                    r.key(b" ")
                    r.pump(0.3)
                    if r.player():
                        route.add(r.player())
                    return None if r.over() else held
            continue
        one_cell(r, dir_of(p, path[0]))
    return None

# --- title: space does nothing, quit invents no gems ---
r = Run([PROG])
r.pump(0.45)
r.key(b" ", 0.45)
check("space on the title does not start or end the run",
      r.alive() and not r.over() and "press an arrow key" in r.text() and r.score() == 0)
r.quit()
tail = r.log.decode("utf-8", "replace")
cut = tail.rfind("\x1b[2J")
check("quit before the first move prints no share",
      "best of" not in tail[cut:] and not re.search(r"[🟩🟨🟧]", tail[cut:]))

# --- WASD and HJKL steer, P pauses ---
r = Run([PROG])
r.pump(0.4)
p0 = r.player()
r.key(b"d", 0.35)
p1 = r.player()
check("WASD steers", p0 and p1 and p1[0] > p0[0], f"{p0} -> {p1}")
r.key(b"w", 0.35)
p2 = r.player()
check("W steers up", p2 and p1 and p2[1] < p1[1], f"{p1} -> {p2}")
r.key(b"p", 0.3)
held, line, gh = r.player(), r.screen.display[0], r.ghosts()
paused = "PAUSED" in r.text() and r.alive() and not r.over()
r.pump(0.7)
check("P pauses: player, fuse, and ghosts stay, and the run stays alive",
      paused and r.alive() and not r.over() and "PAUSED" in r.text() and r.player() == held
      and r.screen.display[0] == line and r.ghosts() == gh,
      f"paused {paused} at {r.player()} was {held} fuse {r.fuse()}")
r.key(b"p", 0.35)
check("P resumes", "PAUSED" not in r.text() and not r.over() and r.alive())
r.quit()

r = Run([PROG])
r.pump(0.4)
p0 = r.player()
r.key(b"l", 0.35)
p1 = r.player()
r.key(b"k", 0.35)
p2 = r.player()
check("HJKL steers", p0 and p1 and p2 and p1[0] > p0[0] and p2[1] < p1[1], f"{p0} {p1} {p2}")
r.quit()

# --- wall, retry, 0-gem share ---
r = Run([PROG])
r.pump(0.4)
r.heading = "w"
r.key(ARROW["w"])
for _ in range(30):
    r.pump(0.08)
    if r.over():
        break
over_line = r.text()
check("a wall ends the attempt and shows that attempt's gems",
      "GAME OVER: 0 GEMS" in over_line and r.score() == 0)
r.key(b"r", 0.45)
check("R after game over returns to a new attempt at score 0",
      "press an arrow key" in r.text() and r.score() == 0 and not r.over())
r.key(b"r", 0.3)
check("R on the title does not start the run", "press an arrow key" in r.text() and r.score() == 0)
# start a worse attempt and quit while it is still at 0
r.key(ARROW["d"], 0.35)
check("second attempt is on screen at 0", r.score() == 0 and not r.over() and r.player() and r.player()[0] > 19)
r.quit()
parsed = share_of(r.log)
check("a higher 0 and a lower open attempt: quit reports 0 gems and both tries",
      parsed is not None and parsed[0] is not None and parsed[0].group(2) == "0" and parsed[0].group(3) == "2"
      and parsed[1] == [],
      parsed[2][:80] if parsed else "no share")

# --- one fast grab, ghosts freeze while paused, then a near-empty-fuse grab, quit mid-run ---
r = Run([PROG])
r.pump(0.4)
route = set()
held_gem = grab_one(r, route)
if r.player():
    route.add(r.player())
check("first grab is on the board and paused with a full fuse",
      held_gem is not None and "PAUSED" in r.text() and r.score() == 1 and r.best() == 1 and r.fuse() == 20
      and not r.over(),
      f"gem {held_gem} score {r.score()} fuse {r.fuse()} paused {'PAUSED' in r.text()}")
snap = (r.player(), r.screen.display[0], tuple(sorted(r.ghosts())))
r.pump(0.7)
check("pause freezes a run that already has a ghost",
      r.alive() and not r.over() and (r.player(), r.screen.display[0], tuple(sorted(r.ghosts()))) == snap)

slow_ok = False
share_block = ""
if held_gem and "PAUSED" in r.text() and not r.over():
    g = held_gem
    neigh = []
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        n = (g[0] + dx, g[1] + dy)
        if 0 <= n[0] < 38 and 0 <= n[1] < 18 and n not in route:
            neigh.append(n)
    neigh = [n for n in neigh if not on_rim(n)]
    if neigh:
        dest = min(neigh, key=lambda n: abs(n[0] - r.player()[0]) + abs(n[1] - r.player()[1]))
        rim = {(x, 0) for x in range(38)} | {(x, 17) for x in range(38)} | {(0, y) for y in range(18)} | {(37, y) for y in range(18)}
        def slow_blocked():
            return route | r.ghosts() | {g} | rim
        path = bfs(r.player(), dest, route | r.ghosts() | {g} | rim)
        if path:
            k0 = dir_of(r.player(), path[0])
            r.heading = k0
            # One step only. A second queued turn fires on the tick after and can leave the path.
            os.write(r.master, b" " + ARROW[k0])
            toward(r, dest, slow_blocked, 80)
            S, O = r.player(), None
            if S:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    n = (S[0] + dx, S[1] + dy)
                    n2 = (n[0] + dx, n[1] + dy)
                    if n == g or n in route or not on_board(n) or on_rim(n) or not on_board(n2):
                        continue
                    O = n
                    break
            t0 = time.time()
            while O and time.time() - t0 < 14 and not r.over() and r.score() == 1 and not (r.fuse() <= 3 and r.player() == S):
                p = r.player()
                one_cell(r, dir_of(p, O if p == S else S))
            if r.player() == O and not r.over():
                one_cell(r, dir_of(r.player(), S))
            p = r.player()
            if p and not r.over() and abs(p[0] - g[0]) + abs(p[1] - g[1]) == 1 and g not in r.ghosts() and r.fuse() <= 3:
                one_cell(r, dir_of(p, g))
                if r.score() == 2 and not r.over():
                    r.key(b" ")  # freeze before the next tick walks past the gem
                    r.pump(0.3)
                slow_ok = r.score() == 2 and not r.over() and r.fuse() == 20
r.quit()
parsed = share_of(r.log)
if parsed:
    share_block = parsed[2]
check("quit mid-run reports the gems just collected, one square each, fast then slow",
      slow_ok and parsed and parsed[0] and parsed[0].group(2) == "2" and parsed[0].group(3) == "1"
      and parsed[1] == ["🟩", "🟧"],
      (share_block[:120] if share_block else "no share") + f" slow_ok={slow_ok}")

# --- higher finished run, then a lower open run, then quit ---
r = Run([PROG])
r.pump(0.4)
route = set()
held = grab_one(r, route)
check("setup grab for the best-of comparison", held is not None and r.score() == 1 and "PAUSED" in r.text())
# resume straight into the nearest wall, away from the new gem when we can
if held and r.player() and not r.over():
    px, py = r.player()
    options = []
    for k, (dx, dy) in DELTA.items():
        x, y = px, py
        crosses = False
        while 0 <= x + dx < 38 and 0 <= y + dy < 18:
            x += dx
            y += dy
            if (x, y) == held:
                crosses = True
                break
        if not crosses:
            options.append(k)
    k = options[0] if options else "d"
    r.heading = k
    os.write(r.master, b" " + ARROW[k])
    r.pump(0.05)
    t0 = time.time()
    while time.time() - t0 < 8 and not r.over():
        r.pump(0.08)
check("driving into a wall after one grab shows that grab", "GAME OVER: 1 GEMS" in r.text() and r.score() == 1)
r.key(b"r", 0.45)
g2 = r.gem_at()
p = r.player()
# step to a neighbor that is not the gem
step = "d"
if p and g2:
    for k, (dx, dy) in DELTA.items():
        n = (p[0] + dx, p[1] + dy)
        if 0 <= n[0] < 38 and 0 <= n[1] < 18 and n != g2:
            step = k
            break
r.heading = None
one_cell(r, step)
check("the lower attempt is still under the best", r.score() == 0 and r.best() == 1 and not r.over(),
      f"score {r.score()} best {r.best()}")
r.quit()
parsed = share_of(r.log)
check("quit after a lower attempt keeps the higher gem count, both tries, and that grab's color",
      parsed and parsed[0] and parsed[0].group(2) == "1" and parsed[0].group(3) == "2" and parsed[1] == ["🟩"],
      parsed[2][:100] if parsed else "no share")

# --- touch the ghost ---
r = Run([PROG])
r.pump(0.4)
route = set()
held = grab_one(r, route)
died_on_ghost = False
if held and r.player() and "PAUSED" in r.text():
    r.key(b" ")  # resume
    r.heading = None
    r.pump(0.05)
    t0 = time.time()
    while time.time() - t0 < 8 and not r.over():
        p = r.player()
        gh = r.ghosts()
        if not p or not gh:
            r.pump(0.05)
            continue
        hit = [c for c in gh if abs(c[0] - p[0]) + abs(c[1] - p[1]) == 1]
        if hit:
            one_cell(r, dir_of(p, hit[0]))
            continue
        nearest = min(gh, key=lambda c: abs(c[0] - p[0]) + abs(c[1] - p[1]))
        blocked = {held}
        path = bfs(p, nearest, blocked)
        if not path:
            r.pump(0.05)
            continue
        one_cell(r, dir_of(p, path[0]))
    died_on_ghost = r.over() and r.score() == 1 and "GAME OVER: 1 GEMS" in r.text()
check("touching the ghost ends the run and keeps that gem", died_on_ghost, r.screen.display[0])
r.quit()

# --- two launches, same day number and same first gem; practice is labelled ---
gems = []
days = []
for argv in ([PROG], [PROG], [PROG, "-r"]):
    r = Run(argv)
    r.pump(0.5)
    gems.append(r.gem_at())
    m = re.search(r"#(\d+)", r.screen.display[0])
    days.append(m.group(1) if m else r.screen.display[0][:24])
    label = r.screen.display[0]
    if argv == [PROG, "-r"]:
        check("practice mode is labelled and is not the daily board",
              "practice" in label and "#" not in label.split("fuse")[0])
    r.quit()
check("two launches share the day number and the first gem",
      gems[0] is not None and gems[0] == gems[1] and days[0] == days[1] and days[0].isdigit(),
      f"gems {gems[:2]} days {days[:2]}")

print(f"\n{sum(results)}/{len(results)} share checks passed")
sys.exit(0 if all(results) else 1)
