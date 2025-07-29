"""
DerivaDEX Order Book (L2)
"""

import copy
import logging
from collections import defaultdict, deque
from typing import Optional

import numpy as np
from attrs import define, field
from ddx._rust.common.enums import OrderSide
from ddx._rust.common.state import BookOrder
from ddx._rust.common.state.keys import BookOrderKey
from ddx._rust.decimal import Decimal

logger = logging.getLogger(__name__)


@define
class OrderBook:
    """
    Defines an OrderBook.

    An order book is tied to a given market, and contains both L2 and L3
    information. An L2 order book is an aggregate view of the market,
    providing information regarding unique price levels and total
    quantities at those price levels. L3 order books maintain
    order-by-order, granular data. Users could query the SMT to obtain
    order book data (by querying the BookOrder leaves), however this
    local order book allows for faster and more intuitive querying for
    use by any trader clients.

    Attributes
        _book_orders (dict[BookOrderKey, BookOrder]): Mapping of book order keys to book orders
        _bid_keys (dict[Decimal, deque[BookOrderKey]]): Mapping of bid price levels to FIFO order queues of book order keys (L3)
        _ask_keys (dict[Decimal, deque[BookOrderKey]]): Mapping of ask price levels to FIFO order queues of book order keys (L3)
        _bids (dict[Decimal, Decimal]): Mapping of bid price levels to aggregate quantities (L2)
        _asks (dict[Decimal, Decimal]): Mapping of ask price levels to aggregate quantities (L2)
    """

    _book_orders: dict[BookOrderKey, BookOrder] = field(factory=dict, init=False)
    _bid_keys: dict[Decimal, deque[BookOrderKey]] = field(
        factory=lambda: defaultdict(deque), init=False
    )
    _ask_keys: dict[Decimal, deque[BookOrderKey]] = field(
        factory=lambda: defaultdict(deque), init=False
    )
    _bids: dict[Decimal, Decimal] = field(
        factory=lambda: defaultdict(Decimal), init=False
    )
    _asks: dict[Decimal, Decimal] = field(
        factory=lambda: defaultdict(Decimal), init=False
    )

    @property
    def best_bid_px(self) -> Optional[Decimal]:
        """
        Property returning the best available (highest) bid price.
        """

        return max(list(self._bids.keys())) if self._bids else None

    @property
    def best_ask_px(self) -> Optional[Decimal]:
        """
        Property returning the best available (lowest) ask price.
        """

        return min(list(self._asks.keys())) if self._asks else None

    @property
    def mid_px(self) -> Optional[Decimal]:
        """
        Property returning the mid price for the market.
        """

        if self._bids and self._asks:
            return np.mean([self.best_bid_px, self.best_ask_px])
        elif self._bids:
            return self.best_bid_px
        elif self._asks:
            return self.best_ask_px
        return None

    @property
    def book_orders(self) -> dict[BookOrderKey, BookOrder]:
        """
        Property returning the book orders.
        """
        return copy.deepcopy(self._book_orders)

    @property
    def ask_keys(self) -> dict[Decimal, deque[BookOrderKey]]:
        """
        Property returning the ask keys.
        """
        return copy.deepcopy(self._ask_keys)

    @property
    def bid_keys(self) -> dict[Decimal, deque[BookOrderKey]]:
        """
        Property returning the bid keys.
        """
        return copy.deepcopy(self._bid_keys)

    @property
    def asks(self) -> dict[Decimal, Decimal]:
        """
        Property returning the asks.
        """
        return copy.deepcopy(self._asks)

    @property
    def bids(self) -> dict[Decimal, Decimal]:
        """
        Property returning the bids.
        """
        return copy.deepcopy(self._bids)

    def swap_book_order(self, book_order_key: BookOrderKey, book_order: BookOrder):
        """
        Swap a book order in the local order book.
        Parameters
        ----------
        book_order_key : BookOrderKey
            Book order key for the book order
        book_order : BookOrder
            Book order being stored
        """
        book_order = copy.deepcopy(book_order)
        sided_l2_book, sided_l3_book_keys = (
            (self._bids, self._bid_keys)
            if book_order.side == OrderSide.Bid
            else (self._asks, self._ask_keys)
        )

        # Append this book order key to the back of the L3 order
        # book's queue at that price level if not already present
        if book_order_key not in sided_l3_book_keys[book_order.price]:
            sided_l3_book_keys[book_order.price].append(book_order_key)

        # Increment the aggregate L2 order book amount for this
        # price level by the difference in the swapped book order
        sided_l2_book[book_order.price] += book_order.amount - (
            self._book_orders[book_order_key].amount
            if book_order_key in self._book_orders
            else Decimal("0")
        )

        # Add book order to book order dict.
        self._book_orders[book_order_key] = book_order
        logger.info(
            f"Swapped book order {book_order_key} in order book with {book_order}"
        )

    def remove_book_order(
        self,
        book_order_key: BookOrderKey,
    ):
        """
        Remove a book order from the local order book.
        Parameters
        ----------
        book_order_key : BookOrderKey
            Book order key for the book order
        """

        # Obtain the book order leaf
        book_order = self._book_orders[book_order_key]

        sided_l2_book, sided_l3_book_keys = (
            (self._bids, self._bid_keys)
            if book_order.side == OrderSide.Bid
            else (self._asks, self._ask_keys)
        )

        # Remove the book order from the L3 order book
        sided_l3_book_keys[book_order.price].remove(book_order_key)

        # Decrement the aggregate L2 order book amount for this price
        # level
        sided_l2_book[book_order.price] -= book_order.amount
        if sided_l2_book[book_order.price] == Decimal("0"):
            # Ensure that we have deleted the L3 order book index above
            if len(sided_l3_book_keys[book_order.price]) != 0:
                raise Exception(
                    "mismatching L2 and L3 order books: l2 signals a price level deletion, but l3 still contains orders at that price"
                )

            # Delete the L3 and L2 price level
            del sided_l3_book_keys[book_order.price]
            del sided_l2_book[book_order.price]

        # Remove the book order from the book order dict.
        del self._book_orders[book_order_key]
        logger.info(f"Removed book order {book_order_key} from order book")
