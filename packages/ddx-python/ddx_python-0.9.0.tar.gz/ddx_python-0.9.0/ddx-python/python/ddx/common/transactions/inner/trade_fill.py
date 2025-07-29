"""
TradeFill module
"""

import asyncio

from attrs import define, field
from ddx.common.transactions.inner.fill import Fill
from ddx.common.transactions.inner.outcome import Outcome
from ddx._rust.common import ProductSymbol
from ddx._rust.common.enums import OrderSide
from ddx._rust.common.state import DerivadexSMT, Price
from ddx._rust.common.state.keys import BookOrderKey, PriceKey
from ddx._rust.decimal import Decimal


@define(hash=True)
class TradeFill(Fill):
    """
    Defines a TradeFill
    """

    maker_order_hash: str = field(eq=str.lower)
    maker_outcome: Outcome = field(hash=False)
    maker_order_remaining_amount: Decimal = field(hash=False)
    taker_order_hash: str = field(eq=str.lower)
    taker_outcome: Outcome = field(hash=False)
    request_index: int = field(default=-1, eq=False, hash=False)

    def __init__(
        self,
        symbol: ProductSymbol,
        taker_order_hash: str,
        maker_order_hash: str,
        maker_order_remaining_amount: Decimal,
        amount: Decimal,
        price: Decimal,
        taker_side: OrderSide,
        maker_outcome: Outcome,
        taker_outcome: Outcome,
        time_value: int,
        request_index: int = -1,
    ):
        """
        Initialize a TradeFill instance
        Parameters
        ----------
        symbol : ProductSymbol
            Product symbol
        taker_order_hash : str
            Taker order hash
        maker_order_hash : str
            Maker order hash
        maker_order_remaining_amount : Decimal
            Maker order remaining amount
        amount : Decimal
            Amount
        price : Decimal
            Price
        taker_side : OrderSide
            Taker side
        maker_outcome : Outcome
            Maker outcome
        taker_outcome : Outcome
            Taker outcome
        time_value : int
            Time value
        request_index : int
            Request index
        """
        super().__init__(
            symbol,
            amount,
            price,
            taker_side,
            time_value,
            request_index,
        )
        self.maker_order_hash = maker_order_hash
        self.maker_outcome = maker_outcome
        self.maker_order_remaining_amount = maker_order_remaining_amount
        self.taker_order_hash = taker_order_hash
        self.taker_outcome = taker_outcome

    def process_tx(
        self,
        smt: DerivadexSMT,
        **kwargs,
    ):
        """
        Process a TradeFill transaction. These are Fill transactions
        that have risen from either a CompleteFill or a PartialFill
        transaction.

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        **kwargs
            Additional args specific to CompleteFill/PartialFill transactions
        """

        maker_book_order_key: BookOrderKey = BookOrderKey(
            self.symbol, self.maker_order_hash
        )
        maker_book_order = smt.book_order(maker_book_order_key)
        maker_book_order_time_value = maker_book_order.time_value

        maker_book_order.amount = self.maker_order_remaining_amount
        smt.store_book_order(maker_book_order_key, maker_book_order)

        # Make the appropriate adjustments for both the maker and taker
        # components of the Trade
        self.adjust_for_maker(
            smt,
            kwargs["epoch_id"],
            kwargs["trade_mining_active"],
            maker_book_order_time_value,
        )
        self.adjust_for_taker(
            smt,
            kwargs["epoch_id"],
            kwargs["trade_mining_active"],
            maker_book_order_time_value,
        )
