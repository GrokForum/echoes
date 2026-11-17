/* ECHOES - a tiny terminal arcade game. No libc, x86-64 Linux.
   Every gem you grab leaves a ghost that walks the route you just took,
   back and forth, forever. Touch any ghost (or a wall) and it's over.
   Screen -> fd 2 (your terminal). Optional soft sine sound -> fd 1 (u8 mono 32 kHz, piped to aplay). */
#define N __attribute__((noinline)) static
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned u32;

enum { AW = 38, AH = 18, MAXG = 250, PL = 128, RATE = 32000 };

/* raw Linux syscall, up to 4 args */
N long sc(long n, long a, long b, long c, long d) {
  long r; register long r10 __asm__("r10") = d;
  __asm__ volatile("syscall" : "=a"(r) : "a"(n), "D"(a), "S"(b), "d"(c), "r"(r10) : "rcx", "r11", "memory");
  return r;
}
/* entry: hand the initial stack (argc, argv...) to main */
__asm__(".globl _start\n_start:\n mov %rsp,%rdi\n call main\n");

static u16 pool[MAXG * PL];          /* every ghost's recorded route, as y*64+x */
static u8 glen[MAXG];                /* route length per ghost */
static u32 gbirth[MAXG];             /* tick the ghost was born */
static u16 rec[PL]; static int rn;   /* route being recorded right now */
static u8 grade[MAXG], bgrade[MAXG]; /* speed grade per gem (share grid), and for the best run */
static u8 cell[AH][AW];
static char ob[40000], *p;           /* one frame of escape codes */
static u8 S[256];                    /* sine table */
static u8 au[4096];                  /* audio chunk */
static u32 tio[9], raw[9];           /* struct termios (36 bytes) */
static int px, py, dx, dy, gx, gy, score, best, fuse, fmax, G, state, tries, daily = 1, snd, bestn;
static u32 T, rng, seed, day;
static int qd[4], qn;                /* queued turns */
/* synth */
static u32 ph, step, env, dec; static u16 sq[4], sl[4]; static int sn, si;

N char *str(char *d, const char *s) { while (*s) *d++ = *s++; return d; }
N char *num(char *d, u32 v) { char t[10]; int n = 0; do t[n++] = '0' + v % 10; while (v /= 10); while (n) *d++ = t[--n]; return d; }
N void out(char *e) { sc(1, 2, (long)ob, e - ob, 0); }
N char *at(char *d, int r, int c, const char *s) { d = str(d, "\33["); d = num(d, r); *d++ = ';'; d = num(d, c); *d++ = 'H'; return str(d, s); }

/* sound: queue up to 4 notes (Hz, ms). Gentle: sine, linear fade-out, ~1/4 volume. */
N void tune(int n, int f0, int f1, int f2, int ms) { sq[0] = f0; sq[1] = f1; sq[2] = f2; sn = n; si = 0; env = 0; sl[0] = ms; }
static long t0[2], aw;                /* audio clock start, samples written so far */
N void audio(void) {
  if (!snd) return;
  long ts[2]; sc(228, 1, (long)ts, 0, 0);                /* clock_gettime(CLOCK_MONOTONIC) */
  long due = (ts[0] - t0[0]) * RATE + (ts[1] - t0[1]) / (1000000000 / RATE) + RATE / 25 - aw;  /* real time + 40 ms lead */
  int q = 0; sc(16, 1, 0x541B, (long)&q, 0);             /* FIONREAD: bytes the player hasn't taken yet */
  if (q > RATE / 25) { due -= q - RATE / 25; aw += q - RATE / 25; }  /* player started late: drop, don't lag */
  if (due <= 0) return; if (due > 4096) due = 4096;
  for (int i = 0; i < due; i++) {
    if (env < 256 && si < sn) { step = sq[si] * 134218u; env = 255 << 16; dec = (255 << 16) / (RATE / 1000 * sl[0]); si++; }
    int v = 0;
    if (env >= 256) { v = (((int)S[ph >> 24] - 128) * (int)(env >> 16)) >> 11; env = env > dec ? env - dec : 0; ph += step; }
    au[i] = 128 + v;
  }
  aw += due;
  if (sc(1, 1, (long)au, due, 0) < 0) snd = 0;           /* no player on the other end: go silent */
}

N void rnd(void) { rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5; }
N void newgem(void) { do { rnd(); gx = rng % AW; gy = (rng >> 8) % AH; } while (gx == px && gy == py); }

N void reset(void) {
  px = AW / 2; py = AH / 2; dx = dy = 0; G = score = qn = 0; T = 0; state = 0;
  fmax = fuse = 90; rng = seed; newgem(); rec[0] = py * 64 + px; rn = 1;
}

N int gpos(int i, u32 t) {                                /* where ghost i is at tick t (ping-pong along its route) */
  u32 L = glen[i], per = 2 * L - 2, k = 0;
  if ((int)(t - gbirth[i]) < 0) t = gbirth[i];
  if (L > 1) { k = (t - gbirth[i]) % per; if (k >= L) k = per - k; }
  return pool[i * PL + k];
}

N void die(void) {
  state = 3;
  if (score > best || !tries) { best = score; bestn = score; for (int i = 0; i < score && i < MAXG; i++) bgrade[i] = grade[i]; }
  tries++; tune(3, 392, 330, 262, 170);
}

N void tick(void) {
  if (qn) { int d = qd[0]; for (int i = 1; i < qn; i++) qd[i - 1] = qd[i]; qn--;
    dx = d == 'a' ? -1 : d == 'd' ? 1 : 0; dy = d == 'w' ? -1 : d == 's' ? 1 : 0; }
  px += dx; py += dy; T++;
  if (px < 0 || px >= AW || py < 0 || py >= AH) { px -= dx; py -= dy; die(); return; }
  int me = py * 64 + px;
  if (rn < PL) rec[rn++] = me;
  for (int i = 0; i < G; i++)                             /* ghosts are 3 cells long: head + 2-cell trail */
    if (gpos(i, T) == me || gpos(i, T - 1) == me || gpos(i, T - 2) == me) { die(); return; }
  if (px == gx && py == gy) {
    int used = fmax - fuse;
    grade[score < MAXG ? score : MAXG - 1] = used * 3 / (fmax + 1);
    if (G < MAXG) { for (int i = 0; i < rn; i++) pool[G * PL + i] = rec[i]; glen[G] = rn; gbirth[G++] = T; }
    rec[0] = me; rn = 1; score++;
    fmax = 90 - score; if (fmax < 45) fmax = 45; fuse = fmax;
    newgem();
    int f = 523 + score * 6; if (f > 1046) f = 1046;
    tune(2, f, f * 3 / 2, 0, 80);
  } else if (!--fuse) die();
}

static const char *const gc[6] = { "\33[38;5;104m", "\33[38;5;109m", "\33[38;5;139m", "\33[38;5;144m", "\33[38;5;110m", "\33[38;5;174m" };

N void render(void) {
  for (int y = 0; y < AH; y++) for (int x = 0; x < AW; x++) cell[y][x] = 0;
  if (state) {
    for (int i = 1; i < rn; i++) cell[rec[i] >> 6][rec[i] & 63] = 7;          /* the route you're laying down now */
    for (int i = 0; i < G; i++) for (int j = 2; j >= 0; j--) { int q = gpos(i, T - j); cell[q >> 6][q & 63] = j ? 10 + i % 6 : 1 + i % 6; }
  }
  cell[gy][gx] = 8; cell[py][px] = 9;
  p = str(ob, "\33[H\33[0;1;97m ECHOES \33[0;36m");
  if (daily) { *p++ = '#'; p = num(p, day - 20453); } else p = str(p, "practice");
  p = str(p, "  \33[92m\xe2\x97\x86 \33[1m"); p = num(p, score);
  p = str(p, "\33[0;37m  best "); p = num(p, best);
  p = str(p, "  fuse \33[33m");
  for (int i = 0; i < 20; i++) p = str(p, i * fmax < fuse * 20 ? "\xe2\x96\x88" : "\33[90m\xe2\x96\x91");
  p = str(p, "\33[0m\33[K\n\33[90m\xe2\x94\x8c");
  for (int x = 0; x < AW * 2; x++) p = str(p, "\xe2\x94\x80");
  p = str(p, "\xe2\x94\x90\n");
  for (int y = 0; y < AH; y++) {
    p = str(p, "\33[90m\xe2\x94\x82");
    for (int x = 0; x < AW; x++) {
      int c = cell[y][x];
      if (!c) p = str(p, "  ");
      else if (c < 7) { p = str(p, gc[c - 1]); p = str(p, "\xe2\x96\x92\xe2\x96\x92"); }
      else if (c == 7) p = str(p, "\33[38;5;238m\xc2\xb7 ");
      else if (c >= 10) { p = str(p, gc[c - 10]); p = str(p, "\xe2\x96\x91\xe2\x96\x91"); }
      else if (c == 8) p = str(p, "\33[92m\xe2\x97\x86 ");
      else p = str(p, state == 3 ? "\33[91m\xe2\x96\x88\xe2\x96\x88" : "\33[93m\xe2\x96\x88\xe2\x96\x88");
    }
    p = str(p, "\33[90m\xe2\x94\x82\n");
  }
  p = str(p, "\xe2\x94\x94");
  for (int x = 0; x < AW * 2; x++) p = str(p, "\xe2\x94\x80");
  p = str(p, "\xe2\x94\x98\n\33[0;37m arrows/WASD/HJKL move   space pause   r retry   q quit\33[K\33[1;97m");
  if (state == 0) {
    p = at(p, 7, 20, " EVERY GEM YOU GRAB LEAVES A GHOST ");
    p = at(p, 8, 20, "  THAT WALKS YOUR ROUTE FOREVER.   ");
    p = at(p, 16, 23, " \33[93mpress an arrow key to start\33[97m ");
  } else if (state == 2) p = at(p, 10, 25, " PAUSED - space to resume ");
  else if (state == 3) {
    p = at(p, 9, 26, " GAME OVER: "); p = num(p, score); p = str(p, " GEMS ");
    p = at(p, 11, 26, " r = retry   q = quit ");
  }
  out(p);
}

N __attribute__((noreturn)) void quit(void) {
  sc(16, 0, 0x5402, (long)tio, 0);                       /* TCSETS: give the terminal back */
  p = str(ob, "\33[0m\33[?25h\33[2J\33[H");
  if (tries) {
    if (daily) { p = str(p, "ECHOES #"); p = num(p, day - 20453); } else p = str(p, "ECHOES practice");
    p = str(p, " \xe2\x96\xb8 "); p = num(p, best); p = str(p, " gems, best of "); p = num(p, tries);
    p = str(p, tries > 1 ? " tries\n" : " try\n");
    for (int i = 0; i < bestn && i < 50; i++) {        /* green = fast grab, yellow = ok, orange = slow */
      p = str(p, bgrade[i] == 0 ? "\xf0\x9f\x9f\xa9" : bgrade[i] == 1 ? "\xf0\x9f\x9f\xa8" : "\xf0\x9f\x9f\xa7");
      if (i % 10 == 9) *p++ = '\n';
    }
    if (bestn % 10 || bestn > 50) *p++ = '\n';
  }
  out(p); sc(60, 0, 0, 0, 0); for (;;);
}

__attribute__((noreturn, used)) void main(long *sp) {
  for (long i = 2; i <= sp[0]; i++)                      /* flags: -s sound, -r random practice board */
    for (char *a = (char *)sp[i]; *a; a++) { if (*a == 's') snd = 1; if (*a == 'r') daily = 0; }
  u16 ws[4];
  if (sc(16, 2, 0x5413, (long)ws, 0) == 0 && (ws[1] < 78 || ws[0] < 23)) {
    p = str(ob, "ECHOES needs a terminal at least 80 columns x 24 rows. Make the window bigger and try again.\n");
    out(p); sc(60, 1, 0, 0, 0);
  }
  for (int i = 0; i < 256; i++) { int x = i & 127, v = x * (127 - x) >> 5; S[i] = i < 128 ? 128 + v : 128 - v; }
  u32 t = sc(201, 0, 0, 0, 0); day = t / 86400;          /* daily board changes at 00:00 UTC */
  seed = daily ? day * 2654435761u ^ 0x5EED : t * 2654435761u | 1;
  sc(16, 0, 0x5401, (long)tio, 0);                       /* TCGETS */
  for (int i = 0; i < 9; i++) raw[i] = tio[i];
  raw[0] &= ~0x500u;                                     /* -IXON -ICRNL */
  raw[3] &= ~0x800Bu;                                    /* -ISIG -ICANON -ECHO -IEXTEN: Ctrl-C arrives as a key */
  ((u8 *)raw)[17 + 6] = 0; ((u8 *)raw)[17 + 5] = 0;      /* VMIN=0 VTIME=0: non-blocking reads */
  sc(16, 0, 0x5402, (long)raw, 0);
  p = str(ob, "\33[?25l\33[2J"); out(p);
  if (snd) { long ign[4] = { 1, 0, 0, 0 }; sc(13, 13, (long)ign, 0, 8); tune(1, 523, 0, 0, 150); sc(228, 1, (long)t0, 0, 0); }  /* ignore SIGPIPE, start audio clock */
  reset();
  long ts[2] = { 0, 20000000 }; char ib[64];
  for (;;) {
    for (int s = 0; s < 5; s++) {                        /* 5 x 20 ms slices per 100 ms game tick */
      long n = sc(0, 0, (long)ib, 64, 0);
      for (long i = 0; i < n; i++) {
        int c = ib[i];
        if (c == 27 && i + 2 < n && ib[i + 1] == '[') { c = ib[i + 2]; i += 2; c = c == 'A' ? 'w' : c == 'B' ? 's' : c == 'C' ? 'd' : c == 'D' ? 'a' : 0; }
        if (c >= 'A' && c <= 'Z') c += 32;
        c = c == 'k' ? 'w' : c == 'j' ? 's' : c == 'h' ? 'a' : c == 'l' ? 'd' : c;
        if (c == 'q' || c == 3) quit();
        if (c == 'w' || c == 'a' || c == 's' || c == 'd') {
          if (state == 0) state = 1;
          if (state == 1 && qn < 4) qd[qn++] = c;
        } else if (c == ' ' || c == 'p') { if (state == 1) state = 2; else if (state == 2) state = 1; }
        else if ((c == 'r' || c == 13) && state == 3) reset();
      }
      audio();
      sc(35, (long)ts, 0, 0, 0);
    }
    if (state == 1) tick();
    render();
  }
}
