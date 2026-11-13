"""Reproducible synthetic fill simulator, not a predictive trading backtest."""
from __future__ import annotations

import random
from dataclasses import dataclass

from .core import Fill, Hedger, Ledger, Metrics, Quoter, RiskPolicy, RiskTracker, Side


@dataclass(frozen=True)
class SimulationConfig:
    steps: int = 1_000
    seed: int = 42
    initial_mid_cents: int = 10_000
    maker_fill_probability: float = 0.18
    hedge_slippage_cents: int = 2
    tick_cents: int = 1

    def __post_init__(self) -> None:
        if self.steps <= 0 or self.initial_mid_cents <= 0 or self.tick_cents <= 0:
            raise ValueError("steps and prices must be positive")
        if not 0 <= self.maker_fill_probability <= 0.5:
            raise ValueError("maker fill probability must be between 0 and 0.5")
        if self.hedge_slippage_cents < 0:
            raise ValueError("hedge slippage cannot be negative")


def simulate(config: SimulationConfig, policy: RiskPolicy | None = None) -> Metrics:
    """Process market move, maker order, hedge action and risk measurement.

    Each maker fill is one unit. Quotes are not guaranteed to execute. The
    synthetic fill probability is independent of price, so results are strictly
    educational and must not be interpreted as realistic profitability.
    """
    rng = random.Random(config.seed)
    risk = policy or RiskPolicy()
    quoter = Quoter(risk, tick_cents=config.tick_cents)
    hedger = Hedger(risk)
    ledger = Ledger()
    tracker = RiskTracker()
    midpoint = config.initial_mid_cents
    maker_fills = 0
    hedge_fills = 0

    for _ in range(config.steps):
        midpoint = max(config.tick_cents, midpoint + rng.choice((-1, 0, 1)) * config.tick_cents)
        quote = quoter.quote(midpoint, ledger.position)
        event = rng.random()
        if event < config.maker_fill_probability and quote.bid_size:
            ledger.apply(Fill(Side.BUY, 1, quote.bid))
            maker_fills += 1
        elif event < 2 * config.maker_fill_probability and quote.ask_size:
            ledger.apply(Fill(Side.SELL, 1, quote.ask))
            maker_fills += 1

        tracker.observe(ledger.position)  # Record intrastep exposure BEFORE hedging.
        hedge_quantity = hedger.desired_trade(ledger.position)
        if hedge_quantity:
            side = Side.BUY if hedge_quantity > 0 else Side.SELL
            hedge_price = midpoint + (config.hedge_slippage_cents * side.value)
            hedge_price = max(config.tick_cents, hedge_price)
            ledger.apply(Fill(side, abs(hedge_quantity), hedge_price))
            hedge_fills += 1
        tracker.observe(ledger.position)

    return Metrics(
        equity_cents=ledger.equity_cents(midpoint),
        max_abs_position=tracker.max_abs_position,
        average_abs_position=tracker.average_abs_position,
        maker_fills=maker_fills,
        hedge_fills=hedge_fills,
        final_position=ledger.position,
        mark_price=midpoint,
    )
