"""
MarketDataDriver module.
"""

import copy
import datetime
import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

from aiohttp import ClientSession
from attrs import define, field
from ddx.common.logging import data_logger
from ddx._rust.common import ProductSymbol
from ddx._rust.common.requests import (AdvanceEpoch, AdvanceSettlementEpoch,
                                        AdvanceTime, IndexPrice,
                                        MintPriceCheckpoint, SettlementAction,
                                        UpdateProductListings)
from ddx._rust.common.specs import Quarter
from ddx._rust.decimal import Decimal
from sortedcontainers import SortedSet
from tests.harness.market_data_driver.tick import Tick, TickedTxResponsesType

if TYPE_CHECKING:
    from tests.harness.store import Store

logger = data_logger(__name__)


def finished_quarter(
    quarters: SortedSet[Quarter],
    before_time: datetime.datetime,
    current_time: datetime.datetime,
) -> Optional[Quarter]:
    logger.info(f"Finished quarter? {before_time} => {current_time}")

    for quarter in quarters:
        friday = quarter.expiry_date_after(before_time)
        logger.debug(f"Checking upcoming quarter {quarter} expiry {friday}")
        if friday <= current_time:
            return quarter
    return None


@define
class MarketDataDriver(ABC):
    """
    Defines a MarketDataDriver.

    A MarketDataDriver is responsible for generating market data to drive the simulation.

    Attributes:
        symbols_feed (dict[ProductSymbol, str]): Symbol <> underlying price ticker mapping.
        start_timestamp (datetime.datetime): Initial timestamp for market data.
        time_frame (str): Initial sampling frequency for market data which will then be upsampled to 1s.
        client (ClientSession): HTTP client connection.
        store (Store): Store instance.
    """

    symbols_feed: dict[ProductSymbol, str]
    start_timestamp: datetime.datetime
    time_frame: str
    client: ClientSession
    store: "Store" = field(init=False)

    def __attrs_post_init__(self):
        from tests.harness.store import Store

        # Get initialized store instance.
        self.store = Store.the_store()

    @abstractmethod
    def generate_df(self):
        """
        Generate a market data dataframe to drive the simulation. This function is implemented uniquely by the
        various types of MarketDataDrivers.
        """
        pass

    async def ticks(self):
        """
        Async generator to drive market data. Each cycle accomplishes several things:
            1) Iterate through each row of the market data (1s frequency).
            2) Submit an AdvanceTime command to advance the operator's clock by 1s.
            3) Evaluate whether a PriceCheckpoint command must be sent at the appropriate interval.
            4) Evaluate whether an AdvanceSettlementEpoch command must be sent at the appropriate interval.
            5) Evaluate whether an AdvanceEpoch command must be sent at the appropriate interval.
            6) Evaluate each symbol's close price for whether it has breached the 1bps deviation threshold.
            7) Submit a new IndexPrice command to the operator when appropriate.
            8) Yield the market data tick, consisting of the timestamp, symbol, and new price.
        """
        import tests.python_only

        # Initialize reference price mapping of symbol to baseline reference price to assess deviation threshold (1bps).
        ref_pxs = {}
        ref_px_deviation_threshold = Decimal("0.0001")

        # Generate the market data dataframe depending on the type of driver being used.
        df = self.generate_df()

        for index, row in df.iterrows():
            # Looping through each row of market data (1s frequency).

            # Store responses from operator and reference implementation for test matchers.
            ticked_tx_responses = {}
            # Create a new AdvanceTime command and submit it to the operator, and increment our local clock by 1.
            logger.info(
                f"Time value: {self.store.time_value}, Timestamp: {self.store.timestamp}"
            )
            old_timestamp = self.store.timestamp
            self.store.time_value += 1
            self.store.timestamp = index.to_pydatetime().replace(
                tzinfo=datetime.timezone.utc
            )
            timestamp_in_millis = (
                int(self.store.timestamp.timestamp() * 1000)
                + self.store.timestamp.microsecond // 1000
            )
            advance_time = AdvanceTime(self.store.time_value, timestamp_in_millis)
            await self.store.send_and_audit_request(advance_time)

            logger.info(
                f"New time value: {self.store.time_value}, New timestamp: {self.store.timestamp}"
            )

            lifetimed_products = {
                symbol: product
                for symbol, product in self.store.state.products.items()
                if product.tradable_product.parameters is not None
            }

            prices = {}
            for symbol in self.symbols_feed:
                # Loop through each symbol comprising this row.

                # Retrieve the close px to evaluate.
                new_px = Decimal(str(row[f"{symbol}_close"]))
                if (
                    symbol not in ref_pxs
                    or abs(ref_pxs[symbol] - new_px) / ref_pxs[symbol]
                    > ref_px_deviation_threshold
                ):
                    # Reset reference price.
                    ref_pxs[symbol] = new_px

                    # If the deviation threshold has been crossed, we have a new price to handle...

                    # Create a new IndexPrice command and submit it to the operator.
                    index_price = IndexPrice(
                        symbol,
                        new_px.recorded_amount(),
                        Decimal("0"),
                        symbol.price_metadata(),
                        self.store.time_value,
                    )
                    prices[symbol] = new_px
                    before_local_smt = copy.deepcopy(self.store.state.smt)
                    ticked_tx_responses[TickedTxResponsesType.INDEX_PRICE] = (
                        self.store.state.process_price(index_price),
                        await self.store.send_and_audit_request(
                            index_price,
                            (before_local_smt, self.store.state.root),
                        ),
                    )
                    logger.info(f"IndexPrice: {index_price}")

            if self.store.time_value > 1:
                if (
                    self.store.time_value - 1
                ) % self.store.epoch_params.price_checkpoint_size == 0:
                    # Consider creating a new PriceCheckpoint command and submit it to the operator
                    price_checkpoint = MintPriceCheckpoint(advance_time.value)
                    before_local_smt = copy.deepcopy(self.store.state.smt)
                    ticked_tx_responses[TickedTxResponsesType.PRICE_CHECKPOINT] = (
                        self.store.state.mint_price_checkpoint(),
                        await self.store.send_and_audit_request(
                            price_checkpoint,
                            (before_local_smt, self.store.state.root),
                        ),
                    )
                    logger.info(f"MintPriceCheckpoint: {price_checkpoint}")

                advance_settlement_epoch = None
                if (
                    self.store.time_value - 1
                ) % self.store.epoch_params.settlement_epoch_length == 0:
                    actions = []

                    for (
                        action,
                        length,
                    ) in self.store.epoch_params.settlement_action_periods.items():
                        if (
                            action == SettlementAction.TradeMining
                            and not self.store.is_trade_mining()
                        ):
                            continue
                        # starting all our futures at tick 1 + x (x is the length of the future)
                        if (self.store.time_value - 1) % length == 0:
                            actions.append(action)
                    # Create a new AdvanceSettlementEpoch command and submit it to the operator
                    advance_settlement_epoch = AdvanceSettlementEpoch(
                        self.store.settlement_epoch_id + 1, advance_time, actions
                    )

                quarters = SortedSet(
                    filter(
                        lambda quarter: quarter is not None,
                        map(
                            lambda product: product.tradable_product.parameters.futures_quarter(),
                            lifetimed_products.values(),
                        ),
                    )
                )
                if (
                    quarter := finished_quarter(
                        quarters,
                        old_timestamp,
                        self.store.timestamp,
                    )
                ) is not None:
                    logger.info(f"Finished quarter: {quarter}")
                    advance_settlement_epoch = AdvanceSettlementEpoch(
                        self.store.settlement_epoch_id + 1,
                        advance_time,
                        (
                            advance_settlement_epoch.actions
                            if advance_settlement_epoch is not None
                            else []
                        )
                        + [
                            SettlementAction.PnlRealization,
                            SettlementAction.FuturesExpiry(quarter),
                        ],
                    )

                if advance_settlement_epoch is not None:
                    before_local_smt = copy.deepcopy(self.store.state.smt)
                    ticked_tx_responses[
                        TickedTxResponsesType.ADVANCE_SETTLEMENT_EPOCH
                    ] = (
                        self.store.state.advance_settlement_epoch(
                            advance_settlement_epoch
                        ),
                        await self.store.send_and_audit_request(
                            advance_settlement_epoch,
                            (before_local_smt, self.store.state.root),
                        ),
                    )
                    logger.info(f"AdvanceSettlementEpoch: {advance_settlement_epoch}")

                    self.store.settlement_epoch_id += 1

                old_tradable_products = {
                    product.tradable_product for product in lifetimed_products.values()
                }
                new_tradable_products = {
                    tradable_product
                    for specs_key in self.store.market_specs.keys()
                    if specs_key.has_lifecycle()
                    for tradable_product in specs_key.current_tradable_products(
                        self.store.timestamp
                    )
                }
                if len(old_tradable_products) != len(new_tradable_products):
                    additions = list(new_tradable_products - old_tradable_products)
                    logger.info(f"Additions: {additions}")
                    removals = list(old_tradable_products - new_tradable_products)
                    logger.info(f"Removals: {removals}")
                    update_product_listings = UpdateProductListings(
                        additions,
                        removals,
                    )
                    before_local_smt = copy.deepcopy(self.store.state.smt)
                    ticked_tx_responses[
                        TickedTxResponsesType.UPDATE_PRODUCT_LISTINGS
                    ] = (
                        self.store.state.update_product_listings(
                            update_product_listings
                        ),
                        await self.store.send_and_audit_request(
                            update_product_listings,
                            (before_local_smt, self.store.state.root),
                        ),
                    )
                    logger.info(f"UpdateProductListings: {update_product_listings}")

                if (
                    self.store.time_value - 1
                ) % self.store.epoch_params.epoch_size == 0:
                    # Consider creating a new AdvanceEpoch command and submit it to the operator
                    advance_epoch = AdvanceEpoch(
                        self.store.epoch_id + 1,
                        advance_time,
                    )
                    before_local_smt = copy.deepcopy(self.store.state.smt)
                    ticked_tx_responses[TickedTxResponsesType.ADVANCE_EPOCH] = (
                        self.store.state.advance_epoch(advance_epoch),
                        await self.store.send_and_audit_request(
                            advance_epoch,
                            (before_local_smt, self.store.state.root),
                        ),
                    )
                    logger.info(f"AdvanceEpoch: {advance_epoch}")

                    self.store.epoch_id += 1

            # Yield the market data tick.
            tick = Tick(index, prices, ticked_tx_responses)
            logger.info(f"Tick: {tick}")
            yield tick
