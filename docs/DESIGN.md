# Engineering design and validation

## Scope and invariants

The model intentionally uses synchronous event processing with deterministic random seeds. It avoids pretending to simulate distributed order handling. Cents and integer ticks prevent floating-point price drift. Separate book and recovery examples illustrate additional concepts without changing that execution model. See the [coverage map](PORTFOLIO_COVERAGE.md) for what is runnable and the [case study](CASE_STUDY.md) for the larger private project's design.

Invariants:
1. Every fill quantity and price must be positive.
2. The quote satisfies `0 < bid < ask`, and sizes are non-negative.
3. Maker fills cannot grow a position beyond the configured hard limit when each fill is one unit and the initial position is within bounds.
4. Hedging always decreases absolute exposure and never crosses zero.
5. Equity is cash plus marked inventory; no initial capital is assumed.

## Risk tradeoffs

The quoter reduces the chance of building more inventory at a hard limit by suppressing the exposure-increasing side. The hedger trades off immediacy and simulated slippage. Keeping exposure near zero reduces directional risk, but frequent hedges can consume market-making spread. Here the hedge threshold is deliberately explicit so the tradeoff can be studied.

`max_abs_position` captures brief spikes before hedging. `average_abs_position` is averaged over twice-per-step observations rather than actual elapsed time, so it is not a time-weighted metric.

## Test strategy

Unit tests target numerical accounting and state transitions. Deterministic simulation tests verify repeatability and risk boundaries. No integration tests for an exchange are claimed because this repository does not implement one.

## Known limitations and next steps

1. Replace independent maker-fill probabilities with a queue-aware order-book model.
2. Measure the sensitivity of P&L and position risk over many seeds and market regimes.
3. Add cancellation, stale quote protection, and latency simulation.
4. Integrate partial hedge fills, unknown execution outcomes, and idempotent reconciliation into the simulator. The separate recovery example only demonstrates normalized execution replay in memory.
5. Add explicit transaction fees and capital/margin constraints.

The simulator is unsuitable for demonstrating alpha or expected live profitability until those limitations are addressed.
