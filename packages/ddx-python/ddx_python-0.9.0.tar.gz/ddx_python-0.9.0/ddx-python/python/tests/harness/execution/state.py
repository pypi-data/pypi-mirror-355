"""
State module.
"""

import sys
from typing import Optional
from attrs import define, field

from ddx._rust.common import ProductSymbol, TokenSymbol
from ddx._rust.common.state import (
    BookOrder,
    DerivadexSMT,
    InsuranceFund,
    Position,
    Price,
    Stats,
    Strategy,
    Trader,
)
from ddx._rust.common.state.keys import (
    BookOrderKey,
    PositionKey,
    PriceKey,
    StatsKey,
    StrategyKey,
    TradableProductKey,
)
from ddx._rust.decimal import Decimal
from ddx._rust.h256 import H256

from ddx.common.epoch_params import EpochParams
from ddx.common.logging import local_logger
from ddx.common.market_specs import MarketSpecs
from ddx.common.trade_mining_params import TradeMiningParams
from ddx.common.transactions.price_checkpoint import PriceCheckpoint
import tests.harness.store as store
from tests.harness.execution.block import BlockMixin
from tests.harness.execution.liquidation import LiquidationMixin
from tests.harness.execution.listing import ListingMixin
from tests.harness.execution.matching import MatchingMixin
from tests.harness.execution.settlement import SettlementMixin
from tests.harness.execution.trade_mining import TradeMiningMixin
from tests.harness.execution.trader import TraderMixin
from tests.harness.order_book import OrderBook

logger = local_logger(__name__)


def trace_calls(frame, event, arg):
    if event == "call":
        code = frame.f_code
        func_name = code.co_name

        # Check if the function belongs to the class we're interested in
        if "self" in frame.f_locals and isinstance(frame.f_locals["self"], State):
            logger.debug(f"State.{func_name} CALL: {frame.f_locals}")

    elif (
        event == "return"
        and "self" in frame.f_locals
        and isinstance(frame.f_locals["self"], State)
    ):
        logger.debug(f"State.{frame.f_code.co_name} RETURN: {arg}")

    return trace_calls


@define
class Product:
    tradable_product: TradableProductKey
    order_book: OrderBook = field(factory=OrderBook)
    rolling_price: Optional[PriceCheckpoint] = None
    price_checkpoint: Optional[PriceCheckpoint] = None
    next_book_ordinal: int = 0


# We use mixins to mimic as much as possible the implementation structure of ddxenclave::TrustedState
class State(
    BlockMixin,
    TraderMixin,
    LiquidationMixin,
    MatchingMixin,
    SettlementMixin,
    TradeMiningMixin,
    ListingMixin,
):
    def __init__(
        self,
        smt: DerivadexSMT,
        genesis_params: str,
        market_specs: MarketSpecs,
        epoch_params: EpochParams,
        trade_mining_params: TradeMiningParams,
        collateral_tranches: list[tuple[Decimal, Decimal]],
    ):
        self.smt = smt
        self.collateral_tranches = collateral_tranches

        # Product abstractions
        self.market_specs = market_specs
        self.epoch_params = epoch_params
        self.trade_mining_params = trade_mining_params
        self.products: dict[ProductSymbol, Product] = {
            item[0].as_product_symbol(): Product(item[0])
            for item in self.smt.all_tradable_products()
        }

        # Volume abstractions
        self.traders: set[str] = set()
        self.total_volume = Stats.default()

        # Other data
        self.last_created_checkpoint = None
        self.last_checkpointed_epoch = 0

        # Get initialized store instance.
        self.store = store.Store.the_store()

        # Log State function calls
        sys.settrace(trace_calls)

    @property
    def root(self):
        return self.smt.root()

    def proof(self, key: H256):
        logger.info(f"Generating merkle proof for key {key} and root {self.root}")
        return self.smt.merkle_proof([key])

    def store_stats(self, stats_key: StatsKey, stats: Optional[Stats]):
        # Store into total volume
        if stats is not None:
            self.traders.add(stats_key.trader)
        self.smt.store_stats(stats_key, stats)

    def reset_volume(self):
        logger.info("Resetting volume")
        self.traders = set()
        self.total_volume = Stats.default()

    def is_ahead_of_price_checkpoint(
        self, symbol: str, rolling_price_hash: str
    ) -> bool:
        return (
            rolling_price_hash != price_checkpoint.index_price_hash
            if symbol in self.products
            and (price_checkpoint := self.products[symbol].price_checkpoint) is not None
            else True
        )

    def record_price_checkpoints(
        self, rolling_prices: dict[ProductSymbol, PriceCheckpoint]
    ) -> dict[ProductSymbol, PriceCheckpoint]:
        updated_prices = {}
        for symbol, price_checkpoint in rolling_prices.items():
            if self.is_ahead_of_price_checkpoint(
                symbol, price_checkpoint.index_price_hash
            ):
                self.products[symbol].price_checkpoint = price_checkpoint

                self.smt.store_price(
                    PriceKey(symbol, price_checkpoint.index_price_hash),
                    Price(
                        price_checkpoint.index_price,
                        price_checkpoint.mark_price_metadata,
                        price_checkpoint.ordinal,
                        price_checkpoint.time_value,
                    ),
                )

                updated_prices[symbol] = price_checkpoint
        return updated_prices

    def positions_for_strategy(
        self, strategy_key: StrategyKey
    ) -> dict[ProductSymbol, tuple[Position, PriceCheckpoint]]:
        return {
            symbol: (position, self.products[symbol].rolling_price)
            for symbol in self.products
            if (position := self.smt.position(strategy_key.as_position_key(symbol)))
            is not None
        }

    def store_book_order(
        self,
        book_order_key: BookOrderKey,
        book_order: Optional[BookOrder],
    ):
        # Store into order book abstraction
        if book_order is None or book_order.is_void():
            self.products[book_order_key.symbol].order_book.remove_book_order(
                book_order_key
            )
        else:
            self.products[book_order_key.symbol].order_book.swap_book_order(
                book_order_key, book_order
            )

        self.smt.store_book_order(book_order_key, book_order)
