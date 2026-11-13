import unittest

from trading_lab.core import Fill, Hedger, Ledger, Quoter, RiskPolicy, Side
from trading_lab.simulator import SimulationConfig, simulate


class TradingLabTests(unittest.TestCase):
    def test_cash_position_and_mark_to_market(self):
        ledger = Ledger()
        ledger.apply(Fill(Side.BUY, 2, 100))
        ledger.apply(Fill(Side.SELL, 1, 105))
        self.assertEqual(ledger.position, 1)
        self.assertEqual(ledger.cash_cents, -95)
        self.assertEqual(ledger.equity_cents(110), 15)

    def test_hedger_reduces_only_excess(self):
        hedge = Hedger(RiskPolicy(soft_limit=2, hard_limit=7, max_hedge_size=3))
        self.assertEqual(hedge.desired_trade(2), 0)
        self.assertEqual(hedge.desired_trade(7), -3)
        self.assertEqual(hedge.desired_trade(-5), 3)

    def test_quoter_suppresses_risk_increasing_side(self):
        policy = RiskPolicy(soft_limit=2, hard_limit=5)
        quoter = Quoter(policy)
        self.assertEqual(quoter.quote(10_000, 5).bid_size, 0)
        self.assertEqual(quoter.quote(10_000, -5).ask_size, 0)
        self.assertLess(quoter.quote(10_000, 0).bid, quoter.quote(10_000, 0).ask)

    def test_quoter_skews_to_reduce_inventory(self):
        quoter = Quoter(RiskPolicy())
        self.assertLess(quoter.quote(10000, 2).bid, quoter.quote(10000, 0).bid)
        self.assertGreater(quoter.quote(10000, -2).ask, quoter.quote(10000, 0).ask)

    def test_invalid_fills_rejected(self):
        with self.assertRaises(ValueError):
            Fill(Side.BUY, 0, 100)
        with self.assertRaises(ValueError):
            RiskPolicy(soft_limit=5, hard_limit=5)

    def test_seed_is_reproducible(self):
        config = SimulationConfig(seed=12, steps=50)
        self.assertEqual(simulate(config), simulate(config))

    def test_zero_fill_market_has_no_trades_or_pnl(self):
        result = simulate(SimulationConfig(steps=100, maker_fill_probability=0))
        self.assertEqual(result.maker_fills, 0)
        self.assertEqual(result.hedge_fills, 0)
        self.assertEqual(result.equity_cents, 0)

    def test_risk_enforced_after_each_step(self):
        policy = RiskPolicy(soft_limit=1, hard_limit=3, max_hedge_size=2)
        result = simulate(SimulationConfig(steps=2000), policy)
        self.assertLessEqual(result.max_abs_position, policy.hard_limit)
        self.assertLessEqual(abs(result.final_position), policy.soft_limit)


if __name__ == "__main__":
    unittest.main()
