# Engineering a trading desk under uncertain execution

The larger private project combined a Go market maker, a Python hedger and an
inherited Python momentum taker, communicating through NATS. The engineering
work covered pricing, risk, execution recovery, measurement and operational
verification. This case study describes those contributions without including
the supplied exchange, its protocol or assessment materials.

The runnable application in this repository is a smaller synchronous Python
model. The [coverage map](PORTFOLIO_COVERAGE.md) distinguishes public code from
private implementation experience. The examples added here were written for
this portfolio after reviewing the original; they are not a claim of a
clean-room development process or a verbatim extract of the original source.

## Pricing and order-book engineering

The private quoter reconstructed orders and price levels from market events,
including partial executions and cancellations. It tracked the desk's own
liquidity separately. Pricing used external liquidity to avoid feeding the
desk's quotes back into its own fair value. Crossing checks used the whole
book, because another desk process's resting order could still be matched.
The public `OrderBook` demonstrates this distinction using local objects.

The original fair value used a size-weighted microprice in a tight market and
a midpoint fallback in a wider market. Quote generation combined inventory
skew, size tapering, a hard position limit and a directional lean. The desk's
aggregate exposure could increase caution, but an offsetting sibling position
could not erase a process's own inventory risk.

Quote width responded to volatility and the range of fair value over an
elapsed-time horizon. Measuring changes per message had coupled the risk
estimate to feed activity; moving the range measure to time addressed that
failure. A large warning could not be averaged away by a calm reading of a
different indicator. In a wide external market, taking available width could
override the price skew; inventory sizing and hedging remained separate
controls. This was an explicit tradeoff, not a universal profitability claim.

Stale data, one-sided books and shocks triggered protective behavior. The
order loop reconciled intended and working orders and avoided replacement
for insignificant size changes, preserving queue priority and reducing traffic.
None of these adaptive controls runs inside the public fixed-spread simulator.

## Execution, attribution and inherited-code repairs

The inherited taker required repairs to request routing, signed sell accounting
and partial-execution handling. Added controls included a spread ceiling,
cooldown, usable defaults, instrument discovery and coordination before crossing.
This was maintenance and extension of supplied code, not authorship of the
whole taker.

An order request timing out does not establish that it failed to execute.
Position accounting therefore followed execution events rather than inferring
fills from request success. A partial fill changes exposure only by the
executed quantity. Execution attribution also distinguished the resting and
aggressing sides so the same match was not counted twice.

The public recovery example starts after normalization: each synthetic event
already identifies one account, instrument and signed fill. It deliberately
does not include a parser or the original venue's event conventions.

## Risk, recovery and coordination

The hedger reconstructed every process's exposure from executions and flattened
each contract independently. Offsetting expiries can leave basis risk; summing
them to zero is not equivalent to eliminating exposure.

Small excursions were worked with passive hedges. Larger exposure or a passive
order that remained unfilled led to aggressive execution with bounded sizing
and escalating slippage. Passive-order tracking was reconciled with fills,
preventing already-filled orders from reserving phantom capacity.

The original recovery path paired position checkpoints with a consumed stream
sequence, replayed subsequent events, and checked that retained history still
covered the required sequence. Missing history made the position unreliable
and stopped hedging. A hard-kill test checked actual process recovery against
independently reconstructed positions.

`recovery.py` demonstrates checkpoints, duplicate suppression and fail-closed
sequence checks in memory. Its stream contains only normalized executions in
strict sequence order. A gap includes an out-of-order event and requires
rebuilding from a trusted history. An immutable stream is assumed: a repeated
sequence is ignored, not compared for conflicting payloads. A real adapter
must handle its own filtering, ordering and sequence semantics.

The example has no durable storage, broker consumer, concurrent access or
process-crash test. In a service, position and sequence must be persisted
together, and every order path must enforce the reliable-state gate. It is
not enough to expose a boolean while another task continues placing orders.

Desk processes announced an intended aggressive trade so sibling processes
could cancel the side it would consume and hold it down briefly. Full-book
crossing checks supplied another defense. An independent diagnostic examined
both trade legs to check self-trades rather than trusting the same counters
used by the strategy. Timing-based coordination remains subject to races; it
is not an atomic cross-process execution guarantee.

Instrument metadata drove tick alignment, price bands, order sizes and
position limits. Risk sizing considered filled and resting exposure, and the
quoter and hedger each had a margin share. That was **not a shared desk-wide
reservation controller**: the taker and simultaneous cross-process reservations
were not covered by a single atomic budget.

## Measuring the system independently

The private scorer replayed executions independently of process self-reports,
sorted them chronologically and computed cash, positions and carried risk.
Residual longs were valued at the closing bid and shorts at the ask, with
fallbacks disclosed. Top-of-book liquidation still ignored walking deeper
levels for a large residual.

Time-weighted absolute exposure measured how long risk was carried. Peak
exposure captured brief spikes. These answer different questions. The public
simulator's average is an observation average before and after hedges, not a
time-weighted result.

The analysis also built a combined desk equity curve, maximum drawdown and
worst-window loss. Drawdowns of individual instruments cannot simply be added:
their peaks and troughs need not occur together. The public CLI does not
calculate these private-tool metrics.

Forward markouts separated initial edge from subsequent price drift:

```
edge  = side * (fair_at_fill - execution_price)
drift = side * (fair_later - fair_at_fill)
total = edge + drift
```

Here side is +1 for a buy and -1 for a sell. Analysis split passive and
aggressive fills, excluded observations without a sufficient future horizon,
and examined whether nominal quote distance predicted realized outcomes.
A large displayed distance is not necessarily edge conditional on getting
filled: the quote may execute only after the market moves against it.

Contracts within one fill are not independent decisions. Uncertainty estimates
were corrected to count fills and account for unequal size. Nearby fills still
share price paths, so those intervals did not resolve serial dependence.
Published-book marks could also include the desk's own quotes. Those biases
were disclosed; external-book markouts and block/session resampling remained
unfinished work.

## Experiments and conclusions

Parameter sweeps and regime runs evaluated the whole desk, not only the quoter.
Paired comparisons joined results by seed. Market extensions introduced
configurable moves, shocks, changing liquidity and within-session regime
transitions. Independent random streams per participant removed one source of
scheduler-dependent randomness; a distributed execution remains sensitive to
timing even with seeded inputs. Liquidity recovery after an emptied book was
also repaired in the supplied market. Only these extensions are claimed as
contributions to that inherited simulator.

Two later policies were actually implemented in the private project, despite
older notes listing them as future work:

- **Selective quoting:** per-side heuristic scores, spread-stability gating and
  confidence-scaled sizes. It failed a predeclared participation requirement
  and did not improve both evaluated regimes, so it stayed disabled by default.
- **High-risk pause:** stop when required width exceeds a risk threshold,
  resume below a lower threshold after sustained calm. It was not promoted:
  one regime deteriorated, comparisons lacked enough paired seeds, and an
  older control result lacked the required drawdown metric.

The evaluation rejected attractive averages when participation or evidence
quality failed the decision rule. Earlier profitability conclusions were
withdrawn after measurement corrections. **Profitability was not established
for either the quoter or the desk.** Small average inventory did not prevent
large losses in a crisis regime. Passing position and self-trade checks in
tested sessions established narrower operational properties, not bounded
economic tail risk.

No private experiment outputs or performance figures are reproduced here.
Public simulator results use different synthetic inputs and cannot validate
the private strategy. No original experiments were rerun for this comparison.

## Observability, validation and delivery

An optional read-only HTTP/SSE dashboard displayed market prices, fair value,
per-process positions, desk exposure, risk bands, estimated live P&L,
heartbeats, decision reasons and a deduplicated trade tape. Its P&L was a live
estimate; the replay scorer remained the reference for session measurement.
The monitor could not send trading or desk-control messages and ran behind an
optional Compose profile.

Controlled probes tested routing, partial execution, cancellation selectors,
self-trade behavior, request rates, instrument limits and replay retention.
Their exact venue requests and results remain private. The general method was
to isolate one behavior, observe actual events and turn the resulting finding
into an implementation constraint or test.

Unit tests covered the order book, quoting decisions, hedger, taker, dashboard
and measurement tools. Corrections included chronological ordering, zero-time
handling, effective sample counts and seeded participant randomness. Build
failures were made fatal to experiments so an empty result could not look like
successful execution.

Service images ran checks during builds. Packaging recorded provenance and
verification built and ran from an extracted archive under an isolated project,
catching dependencies on the developer's working tree or caches. The public
repository instead runs its own Python tests in CI and requires no exchange
image, NATS installation or private fixtures.

Further work remained: shared budget reservations, calibrated side scores,
holdout evaluation, external-book marks, depth-aware liquidation, dependence-
aware uncertainty, and more disconnect, cancel/fill race and restart scenarios.
These are limitations, not implemented features.
