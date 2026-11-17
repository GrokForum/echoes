<div align="center">

# ◆ ECHOES

### A whole arcade game in **3,771 bytes**.

*Every gem you grab leaves a ghost that walks your route forever. Don't touch your past.*

![size](https://img.shields.io/badge/size-3%2C771%20bytes-brightgreen?style=for-the-badge)
![budget](https://img.shields.io/badge/budget-4%2C096%20bytes-blue?style=for-the-badge)
![libc](https://img.shields.io/badge/libc-none-orange?style=for-the-badge)
![platform](https://img.shields.io/badge/platform-linux%20terminal-lightgrey?style=for-the-badge&logo=linux&logoColor=white)
![license](https://img.shields.io/badge/license-MIT-yellow?style=for-the-badge)

<img src="assets/echoes.gif" alt="ECHOES gameplay: the player grabs gems while ghosts replay old routes, then the share grid" width="720">

<sub>Real gameplay, recorded from the game's own terminal output (a simple bot is steering). Smaller than this README.</sub>

</div>

---

## ▶ Play in 30 seconds

Linux, x86-64, a terminal of at least 80×24:

```sh
curl -sLO https://raw.githubusercontent.com/GrokForum/echoes/main/game && chmod +x game && ./game
```

or

```sh
git clone https://github.com/GrokForum/echoes && cd echoes && ./game
```

Nothing to install on a normal Linux desktop: it needs only `sh`, `sed`, `stty` and `lzcat` (xz-utils, standard on Ubuntu, Debian, Fedora and Mint). No libc, no network, no files left behind.

| Command | What it does |
|---|---|
| `./game` | **Today's daily board.** Everyone in the world gets the same gems today; a new board at 00:00 UTC. |
| `./game -r` | Practice: a random board every time. |
| `./game -s` | Soft sound: gentle sine chimes at low volume (off by default). Uses `aplay` or `pacat`. |

## 🎮 Controls

| Key | Action |
|---|---|
| Arrows, WASD or HJKL | Steer (you keep moving, like Snake) |
| Space or P | Pause / resume |
| R | Retry after game over |
| Q or Ctrl-C | Quit (your terminal is restored) |

**The trick:** a quick, direct route leaves a short, harmless ghost. A long, wandering route leaves a big patrol across the board. A fuse bar means you can't stall. Every grab, you're deciding what to leave behind for future-you.

## 🟩 Share your daily score

When you quit, ECHOES prints a Wordle-style result you can paste anywhere:

```
ECHOES #321 ▸ 10 gems, best of 1 try
🟩🟩🟩🟩🟩🟩🟨🟨🟩🟩
```

Each square is one gem: 🟩 grabbed fast, 🟨 okay, 🟧 slow. Same day number, same board, so compare with friends.

## 🗜 How it fits in under 4 KB

C with **no standard library** (raw syscalls) → a **hand-made 120-byte ELF header** instead of the linker's → **LZMA** → a **219-byte shell launcher** that unpacks to `/tmp`, runs it, cleans up and restores your terminal.

| Piece | Bytes |
|---|---:|
| ELF header + program header (hand-written, `src/elfhdr.S`) | 120 |
| Machine code (`.text` + startup) | 4,077 |
| Strings and tables (`.rodata`) | 854 |
| Initialised data + alignment | 25 |
| **Uncompressed program (`echoes.elf`)** | **5,076** |
| LZMA stream (`xz --format=lzma -9e`, tuned) | 3,552 |
| Self-extracting launcher (`src/header.sh`) | 219 |
| **`game`, the thing you run** | **3,771** |
| Headroom left under the 4,096-byte budget | 325 |

The ~109 KB of game state (ghost routes, frame buffer) lives in `.bss`, which costs zero bytes on disk.

Rebuild it yourself (gcc + xz); with the toolchain it was made with (gcc 14.2, xz 5.8) the output is byte-identical:

```sh
./build.sh && sha256sum game
# 5663b44df801588cfc7ba8e1239b398f405ff4ee47bdbd7eec4a4e1939296c19  game
```

## 🧪 Tests

The tests play the real game through a pseudo-terminal (25 checks: movement, ghosts, pause, fuse, daily seed, Ctrl-C, terminal restore, quiet sound...):

```sh
pip install pyte
python3 tests/test_game.py && python3 tests/test_extra.py
```

CI runs them on every push and **fails if `game` grows past 4,096 bytes**.

## 📁 What's here

| Path | What it is |
|---|---|
| `game` | **The game.** 3,771 bytes |
| `echoes.elf` | The same game, uncompressed (5,076 bytes). Runs directly, no sound option |
| `src/echoes.c` | Readable, commented source |
| `src/elfhdr.S`, `src/tiny.ld`, `src/header.sh`, `build.sh` | The squeeze: ELF header, linker script, launcher, build |
| `tests/` | Pseudo-terminal play tests |
| `tools/record_gif.py` | Records the GIF above from real play (asciicast → [agg](https://github.com/asciinema/agg)) |
| `extras/` | The runner-up concepts, SONAR and DRIFT |
| `docs/` | Research on tiny games and the concept comparison |

## Credits

Made by an AI bot in a usage game: it researched tiny-game scenes, wrote up three concepts, picked ECHOES, built it, and wrote the tests that play it. Maintained by GrokForum contributors.

Licensed under the [MIT License](LICENSE).
