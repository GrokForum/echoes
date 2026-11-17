#!/usr/bin/env python3
"""Extra checks: Ctrl-C, raw ELF restoring the terminal by itself, fuse burn-out, small terminal,
daily seed is the same for everyone, practice mode differs, sound mode is quiet and paced, sound with no audio player."""
import os, pty, sys, time, select, termios, struct, fcntl, pyte, re
results = []
def check(name, ok, info=""):
    results.append(ok); print(("PASS " if ok else "FAIL ") + name + (f"  ({info})" if info else ""), flush=True)

class Run:
    def __init__(self, argv, rows=24, cols=80, stdout_pipe=False):
        self.master, self.slave = pty.openpty()
        fcntl.ioctl(self.slave, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
        self.before = termios.tcgetattr(self.slave)
        self.audio = None
        if stdout_pipe: self.audio_r, aw = os.pipe()
        self.pid = os.fork()
        if self.pid == 0:
            os.setsid(); fcntl.ioctl(self.slave, termios.TIOCSCTTY, 0)
            for fd in (0, 1, 2): os.dup2(self.slave, fd)
            if stdout_pipe: os.dup2(aw, 1)
            os.execv(argv[0], argv)
        if stdout_pipe: os.close(aw)
        self.screen = pyte.Screen(cols, rows); self.stream = pyte.ByteStream(self.screen); self.log = bytearray(); self.abytes = bytearray()
    def pump(self, t=0.15):
        end = time.time() + t
        while time.time() < end:
            fds = [self.master] + ([self.audio_r] if hasattr(self, "audio_r") else [])
            r, _, _ = select.select(fds, [], [], max(0, end - time.time()))
            for f in r:
                try: d = os.read(f, 65536)
                except OSError: d = b""
                if f == self.master: self.log.extend(d); self.stream.feed(d)
                else: self.abytes.extend(d)
    def key(self, k, t=0.15): os.write(self.master, k.encode() if isinstance(k, str) else k); self.pump(t)
    def text(self): return "\n".join(self.screen.display)
    def gem(self):
        for y in range(2, 20):
            x = self.screen.display[y].find("◆")
            if x >= 0: return ((x - 1) // 2, y - 2)
    def wait(self, t=2):
        end = time.time() + t
        while time.time() < end:
            self.pump(0.1)
            w, st = os.waitpid(self.pid, os.WNOHANG)
            if w: return st
        return None
    def restored(self): return termios.tcgetattr(self.slave) == self.before

# 1 Ctrl-C through the dropper
r = Run(["./game"]); r.pump(0.8); r.key(b"\x1b[C", 0.5); r.key(b"\x03", 0.1); st = r.wait()
check("Ctrl-C quits (dropper)", st is not None and os.WEXITSTATUS(st) == 0)
check("terminal restored after Ctrl-C", r.restored())

# 2 raw ELF (no shell wrapper) restores terminal by itself
r = Run(["./echoes.elf"]); r.pump(0.6); r.key(b"\x1b[B", 0.4); r.key(b"\x03", 0.1); st = r.wait()
check("unpacked echoes.elf runs and Ctrl-C quits", st is not None and os.WEXITSTATUS(st) == 0 and "ECHOES" in r.log.decode("utf8", "replace"))
check("echoes.elf itself restores termios (no stty help)", r.restored())

# 3 fuse burns out if you just circle around
r = Run(["./echoes.elf"]); r.pump(0.6)
seq = [b"\x1b[A", b"\x1b[C", b"\x1b[B", b"\x1b[D"]
t0 = time.time(); i = 0
while time.time() - t0 < 14 and "GAME OVER" not in r.text():
    r.key(seq[i % 4], 0.1); i += 1
check("fuse runs out -> game over (no stalling)", "GAME OVER: 0 GEMS" in r.text(), f"after {time.time()-t0:.1f}s")
r.key("q", 0.2); r.wait()

# 4 too-small terminal: friendly message, terminal untouched
r = Run(["./echoes.elf"], rows=20, cols=60); st = r.wait()
check("small terminal -> friendly message and exit", st is not None and b"at least 80 columns" in r.log and r.restored())

# 5 daily seed: two runs today show the same first gem; practice mode (-r) differs
gems = []
for argv in (["./game"], ["./game"], ["./game", "-r"], ["./game", "-r"]):
    r = Run(argv); r.pump(0.8); gems.append((r.gem(), r.screen.display[0][:22].strip())); r.key("q", 0.2); r.wait()
check("daily board identical across runs", gems[0][0] == gems[1][0], str(gems[:2]))
check("practice mode labelled and randomised", "practice" in gems[2][1] and (gems[2][0] != gems[0][0] or gems[3][0] != gems[0][0]), str(gems[2:]))

# 6 sound mode: audio goes to stdout, quiet and paced in real time
r = Run(["./echoes.elf", "-s"], stdout_pipe=True); r.pump(0.6); r.key(b"\x1b[C", 0.1)
r.abytes.clear(); t0 = time.time(); r.pump(3.0); dt = time.time() - t0
a = r.abytes; rate = len(a) / dt
peak = max(abs(b - 128) for b in a) if a else 0
r.key("q", 0.2); r.wait()
check("sound stream ~32000 samples/s (paced, low latency)", 28000 < rate < 36000, f"{rate:.0f} B/s")
check("sound is soft (peak <= 16 of 127)", peak <= 16, f"peak {peak}")
# start chime amplitude check from whole capture
# 7 sound flag when no audio player exists on the box: game keeps running
r = Run(["./game", "-s"]); r.pump(1.0); r.key(b"\x1b[C", 0.6); alive = r.wait(0.3) is None and "ECHOES" in r.text()
r.key("q", 0.3); st = r.wait(5)
check("-s through the real dropper (aplay or pacat): game runs, quits cleanly, terminal restored", alive and st is not None and r.restored())
print(f"\n{sum(results)}/{len(results)} extra checks passed")
sys.exit(0 if all(results) else 1)
