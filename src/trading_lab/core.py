"""A deliberately small, deterministic event-driven trading model.

All prices and monetary amounts use integer cents. No real broker connectivity.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Side(Enum):
    BUY = 1
    SELL = -1


@dataclass(frozen=True)
class Quote:
    bid: int
    ask: int
    bid_size: int
    ask_size: int

    def __post_init__(self) -> None:
        if self.bid <= 0 or self.ask <= self.bid:
            raise ValueError("quote must have positive prices and bid < ask")
        if min(self.bid_size, self.ask_size) < 0:
            raise ValueError("quote sizes must be non-negative")


@dataclass(frozen=True)
class Fill:
    side: Side
    quantity: int
    price: int

    def __post_init__(self) -> None:
        if self.quantity <= 0 or self.price <= 0:
            raise ValueError("fill quantity and price must be positive")


@dataclass
class Ledger:
    position: int = 0
    cash_cents: int = 0
    fills: int = 0

    def apply(self, fill: Fill) -> None:
        signed_quantity = fill.side.value * fill.quantity
        self.position += signed_quantity
        self.cash_cents -= signed_quantity * fill.price
        self.fills += 1

    def equity_cents(self, mark_price: int) -> int:
        if mark_price <= 0:
            raise ValueError("mark must be positive")
        return self.cash_cents + self.position * mark_price


@dataclass(frozen=True)
class RiskPolicy:
    soft_limit: int = 3
    hard_limit: int = 8
    max_order_size: int = 2
    max_hedge_size: int = 3

    def __post_init__(self) -> None:
        if not (0 <= self.soft_limit < self.hard_limit):
            raise ValueError("risk limits must satisfy 0 <= soft < hard")
        if self.max_order_size <= 0 or self.max_hedge_size <= 0:
            raise ValueError("order sizes must be positive")


@dataclass
class Quoter:
    policy: RiskPolicy
    half_spread_ticks: int = 2
    inventory_skew_ticks: int = 1
    tick_cents: int = 1

    def quote(self, mid: int, inventory: int) -> Quote:
        if mid <= 0 or self.tick_cents <= 0 or self.half_spread_ticks <= 0:
            raise ValueError("mid, tick, half spread must be positive")
        # Work in tick units to avoid floating point or invalid tick alignment.
        midpoint_ticks = mid // self.tick_cents
        reservation = midpoint_ticks - inventory * self.inventory_skew_ticks
        bid_ticks = max(1, reservation - self.half_spread_ticks)
        ask_ticks = max(bid_ticks + 1, reservation + self.half_spread_ticks)
        bid_size = min(self.policy.max_order_size, max(0, self.policy.hard_limit - inventory))
        ask_size = min(self.policy.max_order_size, max(0, self.policy.hard_limit + inventory))
        return Quote(
            bid=bid_ticks * self.tick_cents,
            ask=ask_ticks * self.tick_cents,
            bid_size=bid_size,
            ask_size=ask_size,
        )


@dataclass
class Hedger:
    policy: RiskPolicy

    def desired_trade(self, position: int) -> int:
        """Signed quantity to reduce inventory to the soft-risk band."""
        if abs(position) <= self.policy.soft_limit:
            return 0
        excess = abs(position) - self.policy.soft_limit
        return -((1 if position > 0 else -1) * min(excess, self.policy.max_hedge_size))


@dataclass
class Metrics:
    equity_cents: int
    max_abs_position: int
    average_abs_position: float
    maker_fills: int
    hedge_fills: int
    final_position: int
    mark_price: int


@dataclass
class RiskTracker:
    max_abs_position: int = 0
    sum_abs_position: int = 0
    observations: int = 0

    def observe(self, position: int) -> None:
        absolute = abs(position)
        self.max_abs_position = max(self.max_abs_position, absolute)
        self.sum_abs_position += absolute
        self.observations += 1

    @property
    def average_abs_position(self) -> float:
        return self.sum_abs_position / self.observations if self.observations else 0.0
