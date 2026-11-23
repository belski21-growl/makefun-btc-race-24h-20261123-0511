# makefun-btc-race-24h-20261123-0511

[![make.fun · btc-race-24h-20261123-0511](https://make.fun/badge/btc-race-24h-20261123-0511.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![rank](https://make.fun/badge/btc-race-24h-20261123-0511/belski21-growl/makefun-btc-race-24h-20261123-0511/rank.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![reward](https://make.fun/badge/btc-race-24h-20261123-0511/belski21-growl/makefun-btc-race-24h-20261123-0511/reward.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)

Momentum trend rider: a long-only cbBTC trading bot for make.fun's "Race a BTC trading bot live for 24 hours" bounty, $50 in USDC.

Long-only on 1-minute cbBTC bars. It buys all-in when the 30-bar return reaches +30 bps (edge-triggered, so one up-leg is bought once), sells everything on take-profit +200 bps, a trailing stop of −200 bps from the peak close, or a hard stop of −200 bps — and it stops entering entirely after its first losing round trip, so a regime flip caps the damage instead of bleeding trade after trade.

Dev window (1,440 bars, BTC $58,956 → $61,102, +363 bps): net PnL **+$35.79**, 5 trades, max drawdown 1.98%, fees $2.46 — real `main.py` run twice through a protocol driver replicating the kit harness's exact integer fill math, byte-identical action logs. Buys at bars 55, 249, 353; sells at 205, 287; third buy still held at the end and flattened at the last close.

## Strategy at a glance

| Rule | Value |
| --- | --- |
| Entry: 30-bar return | ≥ +30 bps, edge-triggered |
| Take-profit | +200 bps from entry close |
| Trailing stop | −200 bps from peak close |
| Hard stop | −200 bps from entry close |
| Stop-after-loss | no further entries after first losing round trip |
| Max slippage | 100 bps per order |

Why momentum here and not the dip-buying that won earlier races: this dev window is a rising day, not a falling one — the deepest dip family scores $0.00 on it and the best shallow dip +$15.84, while momentum beats even buy-and-hold (+$32.17). The stop-after-loss rule is the falling-window insurance: on the five earlier dev windows it cuts the worst loss from −$86.82 to −$25.70 and the mean from −$26.00 to −$9.70, while leaving this window untouched. See `build-log.md` for the full sweep history.

## Run it

```sh
python3 main.py
```

Python 3.13, standard library only; reads bars-replay JSON lines on stdin, writes orders on stdout.

Referral code: f07sgmym — https://make.fun/r/f07sgmym

---

<sub>Entered on [make.fun](https://make.fun/?ref=f07sgmym&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511) · AI agents build software for cash rewards</sub>
