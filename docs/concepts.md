# Three tiny-game concepts (terminal, stock Linux, about 1 to 4 KB)

## 1. ECHOES: "Every gem you grab leaves a ghost that walks your route forever." ★ WINNER
- **Core loop:** steer around a fixed 38×18 board and grab the gem. The route you just walked, from the last gem to this one, becomes a ghost that walks that exact route back and forth forever. Touch a ghost or a wall and it's game over. A fuse bar (9 s, shrinking to 4.5 s) means you can't stall.
- **Controls:** arrows, WASD or HJKL to steer (you keep moving like Snake), space to pause, q to quit, r to retry.
- **Why it's addictive:** you make your own difficulty, like Snake's tail but spread through time. **A short, efficient route leaves a short, harmless ghost; a long, wandering route leaves a long patrol that sweeps the board.** Every grab is a small trade-off ("take the long safe way now, and pay for it later"). The board becomes a picture of your own run. Rounds last seconds and restarts are instant.
- **Hooks:** a **daily board** (same gem sequence for everyone, new at 00:00 UTC) and a **Wordle-style share line** on exit: `ECHOES #321 ▸ 14 gems, best of 3 tries` plus 🟩🟨🟧 squares showing how fast each gem was grabbed.
- **What's fresh:** "dodge your past selves" games exist ([Ghost Loop](https://seye7717.itch.io/ghost-loop), [Echo Loop](https://store.steampowered.com/app/4457510/Echo_Loop/)), but those replay whole rounds and cap the ghosts (Ghost Loop allows 7). ECHOES ties **each ghost's size to how efficiently you played**, the ghosts **never go away and have no cap**, and it adds the daily seed and share grid, on a grid in a terminal, in under 4 KB. It is not a clone of any big hit.
- **Size:** the built game is **3,771 bytes** (5,076-byte ELF → 3,552 bytes of LZMA + a 219-byte launcher).

## 2. SONAR: "Find the exit of a pitch-black maze; every ping lights it up for a moment."
- **Core loop:** a daily maze, invisible. Press space to ping: a ring spreads out and briefly reveals walls, then fades. Walk from memory, find the exit, and use as few pings and steps as you can.
- **Controls:** arrows to move, space to ping.
- **Why it's addictive:** a memory and spatial puzzle with a skill score (pings used) and the same maze for everyone each day. Short daily ritual, like Wordle.
- **What's fresh vs existing:** [Dark Echo](https://rac7.com/presskit/sheet.php?p=dark_echo) does sound-revealed levels (hand-made, horror), and daily maze games exist. A ping budget plus a daily seed in a terminal is new-ish, but the core is close to Dark Echo.
- **Size:** maze generation (recursive backtracker) plus the expanding ring is about 1 to 2 KB packed.

## 3. DRIFT: "Tetris with one key: pieces swing like a pendulum; you only choose when to let go."
- **Core loop:** each piece swings left and right above the well on its own. Press space to drop it. Full rows clear and the swing speeds up.
- **Controls:** space (plus q/p).
- **Why it's addictive:** Flappy Bird-style timing on top of Tetris-style stacking, playable one-handed.
- **What's fresh vs existing:** weak. One-button Tetris already exists ([1 Block Tetris](https://jmthomas6.itch.io/1-block-tetris), [One-Button TETRIS](https://ricardo-sdl.itch.io/one-button-tetris)).
- **Size:** about 1.5 to 2.5 KB packed.

## Why ECHOES wins
1. **Most original mechanic of the three.** The effort-to-danger coupling (efficient play gives small ghosts) is a real strategic layer. SONAR and DRIFT are closer to existing games.
2. **It ticks every box from the research:** seconds-long loop, instant retry, simple controls, difficulty you create yourself (Snake), a board that tells your story (Tetris stack), and a daily seed plus share grid (Wordle).
3. **It's a natural fit for the terminal.** It's grid-based, so text cells lose nothing.
4. **Fits the budget easily:** 3,771 bytes, with room for sound.
