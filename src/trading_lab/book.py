"""Selected order-book concepts using local data, without a wire protocol."""
from dataclasses import dataclass

from .core import Side


@dataclass(frozen=True)
class RestingOrder:
    owner: str
    side: Side
    quantity: int
    price: int

    def __post_init__(self) -> None:
        if not self.owner or not isinstance(self.side, Side):
            raise ValueError("owner and a valid side are required")
        if self.quantity <= 0 or self.price <= 0:
            raise ValueError("quantity and price must be positive")


class OrderBook:
    def __init__(self, desk_owners: frozenset[str]):
        self.desk_owners = desk_owners
        self.orders: dict[str, RestingOrder] = {}

    def add(self, order_id: str, order: RestingOrder) -> None:
        if not order_id or order_id in self.orders:
            raise ValueError("a new nonempty order id is required")
        self.orders[order_id] = order

    def reduce(self, order_id: str, quantity: int) -> None:
        order = self.orders[order_id]
        if not 0 < quantity <= order.quantity:
            raise ValueError("reduction must fit the resting quantity")
        if quantity == order.quantity:
            del self.orders[order_id]
        else:
            self.orders[order_id] = RestingOrder(
                order.owner, order.side, order.quantity - quantity, order.price
            )

    def cancel(self, order_id: str) -> None:
        self.orders.pop(order_id, None)

    def best(self, *, external_only: bool = False) -> tuple[int | None, int | None]:
        orders = [o for o in self.orders.values()
                  if not external_only or o.owner not in self.desk_owners]
        bids = [o.price for o in orders if o.side is Side.BUY]
        asks = [o.price for o in orders if o.side is Side.SELL]
        return max(bids, default=None), min(asks, default=None)

    def would_cross(self, side: Side, price: int) -> bool:
        if not isinstance(side, Side) or price <= 0:
            raise ValueError("valid side and positive price are required")
        # Sibling orders still match, even though pricing excludes them.
        bid, ask = self.best()
        if side is Side.BUY:
            return ask is not None and price >= ask
        return bid is not None and price <= bid
