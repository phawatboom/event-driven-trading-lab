"""Run with PYTHONPATH=src python examples/recovery.py (PowerShell: set env first)."""
from trading_lab.core import Fill, Side
from trading_lab.recovery import Execution, ExecutionLedger, HistoryGap


def main() -> None:
    bought = Execution(1, "maker", "DEMO", Fill(Side.BUY, 3, 100))
    hedged = Execution(2, "hedger", "DEMO", Fill(Side.SELL, 2, 101))
    desk = ExecutionLedger()
    desk.apply(bought)
    resumed = ExecutionLedger(desk.checkpoint())
    assert not resumed.apply(bought)
    resumed.apply(hedged)
    assert resumed.net_position("DEMO") == 1
    print("Checkpoint restored; duplicate ignored; desk net position: 1")
    try:
        resumed.check_retention(first_available=4)
    except HistoryGap:
        assert not resumed.reliable
        print("Missing execution detected; trading disabled")


if __name__ == "__main__":
    main()
