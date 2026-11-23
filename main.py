# SPDX-License-Identifier: MIT
"""Momentum trend rider — btc-race-24h-20261123-0511, agent-fun/bars-replay/v1.

Long-only bot on 1-minute cbBTC bars, Python 3.13 stdlib only, through
the kit's own vendor/makefun_bars.py shim (copied byte-for-byte).

The idea, in plain words: this dev window is a rising, trending day
(BTC $58,956 -> $61,102, +363 bps, buy-and-hold +$32.17), not a falling
one. Dip-buying has almost nothing to buy here — the deepest dip family
scores $0.00 on this window, the best shallow dip +$15.84 — while
riding the trend pays. So the bot buys strength, not weakness: when the
30-minute return turns positive it goes all-in, rides the move to a
fixed target or a wide trailing exit, and repeats on the next fresh
up-leg. One hard risk rule caps the damage if the regime flips: the
first round trip that ends in a loss stops all further entries for the
rest of the window. On the five earlier dev windows that rule cuts the
worst loss from -$86.82 to -$25.70 and the mean from -$26.00 to -$9.70,
while leaving this window's +$35.79 untouched (every exit here is a
win), so it is risk control, not a tuned peak.

The trade:
  * BUY all cash when the 30-bar return reaches +30 bps, edge-triggered
    (the signal must have been false on the previous bar, so a single
    up-leg is bought once, not every bar it stays true).
  * SELL everything on the first of: +200 bps from the entry close,
    -200 bps from the best close since entry (trailing stop), or
    -200 bps from the entry close (hard stop).
  * STOP: after a round trip that ends with less cash than it started
    with, no further entries for the rest of the window.
  * Orders fill at the next bar's open; max_slippage_bps 100 on every
    order. At most one order per reply. No orders on warm-up batches
    or on batches with no new CBBTC bar. No clock, no files, no
    environment, no randomness: every decision is integer math on the
    closes seen so far, so two runs on the same data answer alike.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
LOOKBACK_BARS = 30
ENTRY_BPS = 30
TAKE_PROFIT_BPS = 200
TRAIL_BPS = 200
STOP_BPS = 200
MAX_SLIPPAGE_BPS = 100


def bps(now, then):
    """Basis points of `now` against `then`, integer math (scale-free)."""
    return (now - then) * 10000 // then


class Bot:
    def __init__(self):
        self.closes = []            # closes of bars seen, in order
        self.prev_signal = False    # momentum signal on the previous bar
        self.entry_close = None     # close at the bar the buy was decided
        self.peak_close = None      # best close since entry
        self.cash_before_buy = None
        self.dead = False           # set after the first losing round trip
        self.order_no = 0
        self.pending_buy = None     # client_id of a buy awaiting its fill
        self.pending_sell = None    # client_id of a sell awaiting its fill
        self.settling_sell = False  # sell filled; judge it on next batch

    def _next_id(self, side):
        self.order_no += 1
        return "%s%d" % (side, self.order_no)

    def on_batch(self, state, batch):
        if state.warming_up:
            return []
        # Settle the fills this batch reports for orders decided last bar.
        for fill in batch.get("fills", []):
            if fill.get("client_id") == self.pending_buy:
                if fill.get("status") == "rejected":
                    self.entry_close = None
                    self.peak_close = None
                self.pending_buy = None
            if fill.get("client_id") == self.pending_sell:
                if fill.get("status") == "filled":
                    self.settling_sell = True
                    self.entry_close = None
                    self.peak_close = None
                self.pending_sell = None
        # A sell has settled once the position is gone: judge the round
        # trip on cash alone; a loser stops all further entries.
        if self.settling_sell and SYMBOL not in state.positions:
            if self.cash_before_buy is not None and state.cash < self.cash_before_buy:
                self.dead = True
            self.settling_sell = False
            self.cash_before_buy = None
        bars = [b for b in batch.get("bars", []) if b.get("symbol") == SYMBOL]
        if not bars:
            return []
        close = state.close(SYMBOL)
        if close is None:
            return []
        self.closes.append(close)
        holding = state.positions.get(SYMBOL)
        signal = (
            len(self.closes) > LOOKBACK_BARS
            and bps(close, self.closes[-1 - LOOKBACK_BARS]) >= ENTRY_BPS
        )
        orders = []
        if holding is None:
            if signal and not self.prev_signal and not self.dead:
                self.cash_before_buy = state.cash
                self.entry_close = close
                self.peak_close = close
                cid = self._next_id("b")
                self.pending_buy = cid
                orders.append(
                    {
                        "side": "buy",
                        "client_id": cid,
                        "symbol": SYMBOL,
                        "notional_quote_units": state.cash,
                        "max_slippage_bps": MAX_SLIPPAGE_BPS,
                    }
                )
        else:
            if self.peak_close is None or close > self.peak_close:
                self.peak_close = close
            if (
                self.entry_close is not None
                and (
                    bps(close, self.entry_close) >= TAKE_PROFIT_BPS
                    or bps(close, self.peak_close) <= -TRAIL_BPS
                    or bps(close, self.entry_close) <= -STOP_BPS
                )
            ):
                cid = self._next_id("s")
                self.pending_sell = cid
                orders.append(
                    {
                        "side": "sell",
                        "client_id": cid,
                        "symbol": SYMBOL,
                        "qty": holding.qty,
                        "max_slippage_bps": MAX_SLIPPAGE_BPS,
                    }
                )
                # entry_close/peak stay until the fill confirms: a
                # rejected sell must re-fire on the next bar.
        self.prev_signal = signal
        return orders


def main():
    makefun_bars.run(Bot().on_batch)


if __name__ == "__main__":
    main()
