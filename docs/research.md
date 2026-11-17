# Research notes: tiny games and why breakout hits stick

Checked 17 Nov 2026. Each fact links to the page it came from. There are no made-up numbers; where a source only gives a rough figure, these notes do the same.

## 1. Tiny games are a real scene

| Scene | The constraint | Source |
|---|---|---|
| **js13kGames** | A whole browser game (code, art, sound) in a .zip of at most 13,312 bytes. It runs every year from 13 Aug to 13 Sep, and readable source is required. | [rules](https://js13kgames.com/2024/rules), [history](https://dinogame.gg/blog/history-of-js13k-games/) |
| js13k's origin | The founder wanted "something original over popular 1k/4k/10k" contests, so smaller 1k/4k/10k jams came first. | [i-programmer](https://www.i-programmer.info/news/167-javascript/11208-how-much-gameplay-can-you-pack-in-just-13k.html) |
| **BootChess** (2015) | Playable chess in 487 bytes, small enough for a 512-byte floppy boot sector. It beat the 672-byte 1K ZX Chess record from 1982. | [Ars Technica](https://arstechnica.com/gaming/2015/01/squeezing-a-playable-chess-program-into-487-bytes/), [BBC](https://www.bbc.com/news/technology-31028787), [ChessProgramming wiki](https://chessprogramming.org/BootChess) |
| **Boot-sector games** (Oscar Toledo G.) | Space Invaders, Pac-Man-like Pillman, F-Bird (Flappy Bird) and more, each in 512 bytes of x86. | [nanochess/book8088](https://github.com/nanochess/book8088), [Invaders](https://github.com/nanochess/Invaders) |
| **SectorLISP** | A whole LISP interpreter in a 512-byte boot sector. It shows the same "every byte counts" mindset outside games. | [jart/sectorlisp](https://github.com/jart/sectorlisp/) |
| **PICO-8 tweetcarts** | Complete games in 280 characters of code, the length of one tweet. Examples are a 60-tune rhythm game and a 278-character Spike Dislike demake. | [Craig Tinney](https://craigtinney.co.uk/carts/tweetcarts/), [Munro](https://munro.itch.io/tweetcarts), [PICO♪HERO](https://www.lexaloffle.com/bbs/?pid=53887), [Spike Dislike](https://www.lexaloffle.com/bbs/?pid=49060) |
| **Linux terminal games** | bsdgames (snake, worm, tetris-bsd...), 2048-cli, nsnake, ninvaders, moon-buggy. These are normal-sized ncurses programs, not size-coded ones. | [bsd-games](https://github.com/jsm28/bsd-games), [opensource.com](https://opensource.com/life/16/6/terminal-based-games-linux) |

**The gap:** stock Linux has plenty of terminal games, but very few are *size-coded* (no libc, a few KB) **and** built around a modern hook such as a daily seed or a shareable result. That's the gap ECHOES aims at.

## 2. What made the breakout hits addictive

- **Tetris**: Alexey Pajitnov made it in 1984 on an Electronika 60, a computer with no graphics, so the pieces were drawn with text characters. *A text-mode original became one of the biggest games ever.* [Guardian](https://www.theguardian.com/culture/2014/jun/02/how-we-made-tetris), [The Register](https://www.theregister.com/offbeat/2024/06/06/the-tetris-company-celebrates-games-40th-birthday/446137)
- **Snake (Nokia 6110, 1997)**: Taneli Armanto made it for a tiny monochrome screen with little memory, and it came pre-installed on the phone. *One rule (don't hit yourself), and you are the source of the difficulty.* [taneliarmanto.com](https://taneliarmanto.com/nokia-snake)
- **Flappy Bird**: one tap. Dong Nguyen told The Verge it averaged about $50,000 a day from ads. He pulled it in Feb 2014 because it had become "an addictive product", and he called it "designed to play in a few minutes when you are relaxed". *One input, instant restart, brutal but fair.* [The Verge](https://www.theverge.com/2014/2/5/5383708/flappy-bird-revenue-50-k-per-day-dong-nguyen-interview), [Forbes](https://www.forbes.com/sites/lananhnguyen/2014/02/11/exclusive-flappy-bird-creator-dong-nguyen-says-app-gone-forever-because-it-was-an-addictive-product/), [BBC](https://www.bbc.com/news/technology-26114364)
- **Threes → 2048**: Threes took its two creators 14 months. 2048 was a weekend project, built on clones of Threes. *Swipe controls with emergent depth: easy to learn, slow to master.* [Vox](https://www.vox.com/2014/2/21/11623772/hit-ios-puzzle-game-threes-almost-had-monsters-and-sushi), [LA Times](https://www.latimes.com/business/technology/la-fi-tn-2048-hit-game-creator-gabriele-cirulli-20140327-story.html), [Polygon](https://www.polygon.com/2014/3/28/5557840/threes-creators-express-puzzlement-sadness-over-2048-and-rampant/)
- **Wordle**: one puzzle a day, the same for everyone. A player in New Zealand invented the spoiler-free emoji grid on 2 Dec 2021, and Wardle added a Share button on 16 Dec. The NYT says 90 people played on 1 Nov and about 300,000 nearly two months later. The NYT bought it for a price "in the low seven figures". *A daily seed plus a shareable result line spread it through group chats.* [Video Game Canon](https://www.videogamecanon.com/adventurelog/the-history-of-wordle/), [NYT](https://www.nytimes.com/2022/01/31/crosswords/nyt-wordle-purchase.html), [Reuters](https://www.reuters.com/business/media-telecom/new-york-times-acquires-wordle-2022-01-31/)
- **Vampire Survivors**: you only move and the weapons fire themselves. The creator spent $1,100 on pre-made assets, and it became a "multimillion-selling" BAFTA winner. *Minimal input, and the screen grows more dense and chaotic over time.* [Guardian](https://www.theguardian.com/games/2023/aug/04/baftas-video-game-vampire-survivors-luca-galante)

### Takeaways used in the design
1. **A loop of a few seconds and an instant restart** (Flappy Bird, Snake).
2. **1 to 4 inputs**. Depth has to come from the rules, not the controls (Tetris, 2048).
3. **Emergent difficulty you create yourself** (Snake's tail, Tetris's stack).
4. **The same daily challenge for everyone, plus a spoiler-free share line** (Wordle).
5. **Visible build-up**, where the screen tells the story of your run (Vampire Survivors, Tetris).

## 3. Prior-art check (honest)
- "Dodge your past selves" exists in browser games: [Ghost Loop](https://seye7717.itch.io/ghost-loop) (max 7 ghosts, each replays a whole round), [GHOST](https://neuracade.com/games/ghost/), [Echo Loop on Steam](https://store.steampowered.com/app/4457510/Echo_Loop/).
- One-button falling-block games: [1 Block Tetris](https://jmthomas6.itch.io/1-block-tetris), [One-Button TETRIS](https://ricardo-sdl.itch.io/one-button-tetris).
- Daily hidden-path deduction: [Seqle](https://dailygamestoplay.com/games/seqle). Echolocation in the dark: [Dark Echo](https://rac7.com/presskit/sheet.php?p=dark_echo).
- One input steering two snakes: [Mirror Snakes](https://snake2play.com/games/mirror-snakes/), [Google Snake Yin-Yang mode](https://google-snake.fandom.com/wiki/Yin_Yang_Mode).
