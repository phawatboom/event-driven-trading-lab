# Portfolio coverage

This repository presents selected runnable examples and a technical case study
of a larger private trading-system project. It does not contain that project's
complete implementation. A capability described here is not necessarily
implemented by the public simulator.

The comparison reviewed private source snapshot
`992ee00c6aeaedea11211ef18c2b10e2bade0acf`, its commit history, and changes
since the commit recording the supplied materials. File paths below identify
evidence in that reviewed snapshot; they are not links or files to copy here.
Commit history supports the distinction between supplied and added work, but
does not establish publication rights or sole authorship. The development
history records AI assistance.

**Status key:** Runnable = demonstrated by public code and tests. Simplified =
only part of the original capability is runnable. Case study = described in
[CASE_STUDY.md](CASE_STUDY.md), with no public implementation claimed.

## Implementation coverage

| Area of work | Evidence in private project | Public representation | Status |
|---|---|---|---|
| Go quoting service and Python risk service | `strategy/main.go`, `hedger/hedger.py` | Case study: architecture; public simulator is Python and synchronous | Case study |
| NATS publish/subscribe and request/reply integration | `strategy/exchange.go`, service entry points | Architecture and execution discussion | Case study |
| Startup metadata discovery, feed selection, environment configuration and shutdown cancellation | `strategy/main.go`, `strategy/exchange.go` | Operations discussion | Case study |
| Per-instrument tick rounding, price bands, volume and position constraints | `strategy/exchange.go`, `hedger/hedger.py` | `Quoter.quote` shows tick prices and position-limited sizes; other venue constraints described | Simplified |
| Request pacing and order-ID lifecycle | `strategy/exchange.go` | Operations discussion; no transport adapter published | Case study |
| Order-book reconstruction, partial reductions and cancellations | `strategy/book.go` | `book.py` models local add/reduce/cancel; no feed parser | Simplified |
| Separate external liquidity for pricing from full book for crossing safety | `strategy/book.go`, `strategy/quoter.go` | `OrderBook.best`, `OrderBook.would_cross`, regression tests | Runnable |
| Size-weighted microprice with midpoint fallback | `strategy/book.go` | Quoting discussion; public quoter accepts a supplied midpoint | Case study |
| Two-sided inventory price skew | `strategy/quoter.go` | `Quoter.quote` | Simplified |
| Inventory size taper and exposure-increasing side suppression | `strategy/quoter.go` | Position-room sizing and hard cap in `Quoter.quote`; no gradual taper | Simplified |
| Desk-aware inventory lean without masking a seat's own risk | `strategy/quoter.go` | Coordination discussion | Case study |
| Volatility width, elapsed-time range, directional lean and wide-market width tradeoff | `strategy/quoter.go` | Quoting discussion; public spread is fixed | Case study |
| Stale/one-sided data guards and shock stand-aside | `strategy/quoter.go` | Quoting discussion | Case study |
| Live-order reconciliation and avoiding unnecessary cancel/replace | `strategy/quoter.go` | Operations discussion | Case study |
| Execution-derived positions, cash and partial-fill accounting | `hedger/hedger.py`, `taker/taker.py` | `Ledger.apply`, `ExecutionLedger` | Simplified |
| Per-seat, per-contract exposure and desk aggregation | `hedger/hedger.py` | `ExecutionLedger.net_position`; instruments stay separate | Runnable |
| Replay, checkpoint state and duplicate delivery handling | `hedger/hedger.py` | `recovery.py` and `examples/recovery.py`; in-memory example only | Simplified |
| Retention-gap detection and unreliable-state protection | `hedger/hedger.py` | `ExecutionLedger.check_retention`, fail-closed tests | Simplified |
| Passive hedging, urgency/patience escalation and passive-fill reconciliation | `hedger/hedger.py` | Hedging discussion; public `Hedger` only calculates excess reduction | Case study |
| Soft risk band, clip sizing and aggressive hedge cost | `hedger/hedger.py` | `Hedger.desired_trade`, synthetic slippage | Simplified |
| Per-seat margin sizing including resting exposure | `strategy/quoter.go`, `hedger/hedger.py` | Risk discussion; original did not implement a shared desk reservation controller | Case study |
| Cross-seat self-trade prevention and timed side suppression | `strategy/quoter.go`, `hedger/hedger.py`, `taker/taker.py` | Coordination discussion; book example demonstrates one crossing guard | Simplified |
| Repairs to an inherited momentum taker | `taker/taker.py`, `taker/test_taker.py` | Attribution and execution discussion; inherited body excluded | Case study |
| Taker spread/cooldown controls, safe defaults and instrument discovery | `taker/taker.py` | Execution discussion | Case study |
| Empirical protocol/limit/retention probes | `tools/probe_01_basics.py` through `tools/probe_10_jetstream.py`, `tools/exlib.py`, probe runners | Validation discussion; exact private protocol and measured venue facts excluded | Case study |
| Independent execution replay scorer and closing-book liquidation | `tools/score.py` | Measurement discussion; public simulator only marks final midpoint | Case study |
| Peak and time-weighted carried exposure | `tools/score.py` | Public `RiskTracker` gives peak and observation average; time weighting described | Simplified |
| Portfolio equity, maximum drawdown and worst-window loss | `tools/score.py` | Measurement discussion; not computed by public CLI | Case study |
| Forward markout, edge/drift decomposition, passive/aggressive attribution | `tools/markout.py` | Measurement discussion | Case study |
| Fill-based uncertainty, effective sample size and nominal-edge buckets | `tools/markout.py` | Measurement discussion and statistical limitations | Case study |
| Parameter sweeps, regime runs and paired-seed comparison | `tools/sweep.py`, `tools/regime.py`, `tools/compare.py`, result JSON files | Experiment discussion; public CLI supports a single seeded run | Case study |
| Selective side scores, stability gate and confidence-scaled size | `strategy/quoter.go`, `EXPERIMENTS.md` | Implemented experimental option in original, rejected and disabled by default | Case study |
| High-risk pause/resume hysteresis | `strategy/quoter.go`, `EXPERIMENTS.md` | Implemented experimental option in original, rejected and disabled by default | Case study |
| Synthetic market extensions: independent RNGs, configurable moves, changing regimes and liquidity recovery | Changes to supplied `sim/market.py`, `tools/test_tools.py` | Seeded public walk is independently written; original extensions described | Simplified |
| Optional read-only HTTP/SSE dashboard, trade deduplication, health and decision explanations | `dashboard/app.py`, `dashboard/state.py`, `dashboard/static/index.html` | Observability discussion; no public dashboard | Case study |
| Independent self-trade diagnostic | `tools/diagnose_selftrades.py` | Validation discussion | Case study |
| Hard-kill hedger restart test | `tools/test_hedger_restart.py` | Recovery discussion; public tests exercise state restoration, not process failure | Case study |
| Unit tests for strategy, hedger, taker, dashboard and measuring tools | Component test files, `tools/test_tools.py` | Public unit tests cover only public code; original tests described | Simplified |
| Container builds with checks, Compose profiles and isolated optional monitor | Component Dockerfiles, `docker-compose.yml` | Operations discussion; public project uses Python CI | Case study |
| Submission packaging and verification from an extracted archive | `package.sh`, `tools/verify_archive.sh` | Delivery discussion; no private archive or packaging copied | Case study |
| Technical notes, experiment log, corrections and rejected hypotheses | `NOTES.md`, `EXPERIMENTS.md` | Fresh case study; private notes and transcript excluded | Case study |

## Attribution and exclusion boundaries

- The quoting service, hedger, dashboard, probes, measurement tooling, tests and
  packaging are recorded as additions in the development history. Their exact
  source remains private here.
- The taker is inherited code with repairs and added controls. Its first
  committed appearance being an addition does not make its inherited body
  original work.
- The synthetic market was supplied and later extended. Credit applies to the
  extensions, not the entire simulator. Run/setup scripts and baseline
  instrument definitions were also supplied.
- Assessment instructions, protocol specifications, change logs, exercise
  guides, raw transcripts, exchange images, instrument fixtures and private
  experiment outputs are excluded. Probe fixture files and old result JSONs
  are covered by the methods discussion rather than redistributed.
- Git configuration and line-ending rules are repository housekeeping, not
  trading capabilities. Their contents are not needed to demonstrate the work.

## What remains intentionally private

The public examples do not reproduce the Go service, transport integration,
private simulator, live-order state machine, durable checkpoint storage,
passive hedging, dashboard or full analysis harness. Every major implementation
area is represented above, but **implementation parity is not claimed**.

A future independent rebuild can follow the case-study-only rows. Preserve
the status distinction as capabilities become runnable, and do not advertise
an unbuilt component in the public architecture diagram.
