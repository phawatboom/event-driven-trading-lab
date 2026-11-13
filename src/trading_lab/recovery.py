"""In-memory recovery example over a synthetic execution-only stream.

Sequence numbers are contiguous and immutable in this example. This is not an
adapter for any exchange, a durable store, or an exactly-once delivery claim.
"""
from dataclasses import dataclass

from .core import Fill, Ledger


class HistoryGap(ValueError):
    """Trading must stop because the position cannot be reconstructed."""


@dataclass(frozen=True)
class Execution:
    sequence: int
    account: str
    instrument: str
    fill: Fill

    def __post_init__(self) -> None:
        if self.sequence < 1 or not self.account or not self.instrument:
            raise ValueError("positive sequence, account and instrument required")


@dataclass(frozen=True)
class Balance:
    account: str
    instrument: str
    position: int
    cash_cents: int
    fills: int


@dataclass(frozen=True)
class Checkpoint:
    sequence: int
    balances: tuple[Balance, ...]


class ExecutionLedger:
    def __init__(self, checkpoint: Checkpoint | None = None):
        self.sequence = 0
        self.reliable = True
        self.accounts: dict[tuple[str, str], Ledger] = {}
        if checkpoint is not None:
            if checkpoint.sequence < 0:
                raise ValueError("checkpoint sequence cannot be negative")
            self.sequence = checkpoint.sequence
            for b in checkpoint.balances:
                key = (b.account, b.instrument)
                if not b.account or not b.instrument or b.fills < 0 or key in self.accounts:
                    raise ValueError("invalid checkpoint balance")
                self.accounts[key] = Ledger(b.position, b.cash_cents, b.fills)

    def require_reliable(self) -> None:
        if not self.reliable:
            raise HistoryGap("execution history is incomplete; trading is disabled")

    def check_retention(self, first_available: int) -> None:
        self.require_reliable()
        if first_available < 1:
            raise ValueError("first available sequence must be positive")
        if first_available > self.sequence + 1:
            self.reliable = False
            self.require_reliable()

    def apply(self, execution: Execution) -> bool:
        self.require_reliable()
        if execution.sequence <= self.sequence:
            return False
        if execution.sequence != self.sequence + 1:
            self.reliable = False
            self.require_reliable()
        key = (execution.account, execution.instrument)
        self.accounts.setdefault(key, Ledger()).apply(execution.fill)
        self.sequence = execution.sequence
        return True

    def net_position(self, instrument: str) -> int:
        self.require_reliable()
        return sum(v.position for (_, symbol), v in self.accounts.items()
                   if symbol == instrument)

    def checkpoint(self) -> Checkpoint:
        self.require_reliable()
        return Checkpoint(self.sequence, tuple(
            Balance(account, instrument, v.position, v.cash_cents, v.fills)
            for (account, instrument), v in sorted(self.accounts.items())
        ))
