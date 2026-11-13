import unittest

from trading_lab.book import OrderBook, RestingOrder
from trading_lab.core import Fill, Side
from trading_lab.recovery import Execution, ExecutionLedger, HistoryGap


class BookTests(unittest.TestCase):
    def test_external_pricing_excludes_desk_but_crossing_includes_it(self):
        book = OrderBook(frozenset({"maker", "hedger"}))
        book.add("external", RestingOrder("outside", Side.SELL, 4, 110))
        book.add("sibling", RestingOrder("hedger", Side.SELL, 2, 105))
        self.assertEqual(book.best(external_only=True), (None, 110))
        self.assertTrue(book.would_cross(Side.BUY, 106))
        book.reduce("sibling", 1)
        self.assertEqual(book.orders["sibling"].quantity, 1)
        book.reduce("sibling", 1)
        self.assertFalse(book.would_cross(Side.BUY, 106))
        book.cancel("external")
        self.assertEqual(book.best(), (None, None))

    def test_sell_crossing_and_invalid_reductions(self):
        book = OrderBook(frozenset())
        order = RestingOrder("outside", Side.BUY, 2, 100)
        book.add("bid", order)
        self.assertTrue(book.would_cross(Side.SELL, 100))
        self.assertFalse(book.would_cross(Side.SELL, 101))
        for quantity in (0, -1, 3):
            with self.assertRaises(ValueError):
                book.reduce("bid", quantity)
        with self.assertRaises(ValueError):
            book.add("bid", order)


class RecoveryTests(unittest.TestCase):
    def test_restart_and_redelivery_preserve_balances(self):
        desk = ExecutionLedger()
        buy = Execution(1, "maker", "DEMO", Fill(Side.BUY, 3, 100))
        desk.apply(buy)
        snapshot = desk.checkpoint()
        resumed = ExecutionLedger(snapshot)
        self.assertFalse(resumed.apply(buy))
        resumed.apply(Execution(2, "hedger", "DEMO", Fill(Side.SELL, 2, 101)))
        self.assertEqual(resumed.net_position("DEMO"), 1)
        self.assertEqual(resumed.accounts[("hedger", "DEMO")].cash_cents, 202)
        self.assertEqual(snapshot, desk.checkpoint())

    def test_positions_are_not_netted_across_instruments(self):
        desk = ExecutionLedger()
        desk.apply(Execution(1, "maker", "NEAR", Fill(Side.BUY, 2, 100)))
        desk.apply(Execution(2, "maker", "FAR", Fill(Side.SELL, 2, 100)))
        self.assertEqual(desk.net_position("NEAR"), 2)
        self.assertEqual(desk.net_position("FAR"), -2)

    def test_retention_gap_disables_trading_and_checkpointing(self):
        desk = ExecutionLedger()
        desk.check_retention(1)
        with self.assertRaises(HistoryGap):
            desk.check_retention(2)
        for operation in (desk.require_reliable, desk.checkpoint,
                          lambda: desk.net_position("DEMO"),
                          lambda: desk.apply(Execution(1, "maker", "DEMO", Fill(Side.BUY, 1, 100)))):
            with self.assertRaises(HistoryGap):
                operation()

    def test_out_of_order_event_fails_closed_without_mutation(self):
        desk = ExecutionLedger()
        with self.assertRaises(HistoryGap):
            desk.apply(Execution(2, "maker", "DEMO", Fill(Side.BUY, 1, 100)))
        self.assertEqual(desk.sequence, 0)
        self.assertEqual(desk.accounts, {})


if __name__ == "__main__":
    unittest.main()
