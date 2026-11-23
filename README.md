# The World in One Day — 23 November 2026

[![news-image-20261123](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/competitions/news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/mekzibnn/news-world-today-23/rank.svg)](https://make.fun/competitions/news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/reward.svg)](https://make.fun/competitions/news-image-20261123)

Sum up 23 November's world news in one image. 35 stories from 7 regions,
every one dated Monday 23 November 2026 — with a red DATE CHECK box for the
big stories that were *not* Monday's news.

## Top stories

- **Ukraine says it sank Russian corvette Merkury off Libya** — 7 sea drones,
  attack early Sunday, Zelensky announces Monday.
- **Dymer toll rises to 14** as boy, 7, pulled alive from rubble.
- **AI sell-off spreads across Asia; gold jumps past $3,600** — Kospi −2%+,
  gold $3,610/oz, Bitcoin $61,417.

## How it works

`main.py` renders a single 1024×1024 PNG (`entry.png`) with Pillow:
navy masthead, giant serif date, red 3-story sub-headline, 6-number stat
strip, 7-region bar, UTC timeline, 3 big pictorial lead cards, 10 medium
pictorial cards, a world map with numbered pins, 22 numbered briefs, a
red-framed DATE CHECK box, and a sources + certainty-legend footer.

Run it:

```sh
python3 main.py
```

The output honours `$MAKEFUN_OUTPUT_DIR` first, then `$ENTRY_OUTPUT`,
then `/output/entry.png`. Pillow is optional: if it cannot be imported,
or the render fails for any reason, the program falls back to copying the
committed `entry.png` to the output path and exits 0.

## Entry

- Competition: [news-image-20261123](https://make.fun/competitions/news-image-20261123)
- Prize: $100, top 50 · entries close 25 Nov 2026 07:00 WIB
- License: MIT
