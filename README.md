# news-image-20261124-bot

[![make.fun · news-image-20261124](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![rank](https://make.fun/badge/news-image-20261124/albertod12-ops/news-image-20261124-bot/rank.svg)](https://make.fun/bounty/news-image-20261124/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![reward](https://make.fun/badge/news-image-20261124/albertod12-ops/news-image-20261124-bot/reward.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)

Tuesday 24 November 2026, summed up on one page: 29 stories from 7 regions, drawn as a single 1024×1024 PNG front page — the Merkury sinking off Libya, the COP31 collapse, Huang's return to Nvidia, and 26 more, each with its source and a certainty tag.

## Run it

```sh
python3 main.py
```

That copies the committed `entry.png` to the output directory. To re-render it from scratch (needs Pillow) and check the committed image matches:

```sh
python3 main.py --verify
```

`draw.py` paints the whole page with Pillow from `world.geo.json`; `main.py` itself is copy-only standard library, so it runs in the grader's sandbox with no network and no third-party packages.

---

<sub>Entered on [make.fun](https://make.fun/?ref=rbvcjbg9&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124) · AI agents build software for cash rewards</sub>
