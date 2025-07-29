"""
Tick module with test matchers
"""

import logging
from typing import AsyncIterator

from attrs import define
from ddx.common.transactions.funding import Funding
from ddx.common.transactions.futures_expiry import FuturesExpiry
from ddx.common.transactions.pnl_realization import PnlRealization
from ddx.common.transactions.tradable_product_update import TradableProductUpdate
from ddx.common.transactions.trade_mining import TradeMining
from tests.harness.market_data_driver.tick import Tick, TickedTxResponsesType
from tests.harness.matchers.utils import assert_tx_eq

logger = logging.getLogger(__name__)


async def default_match_all_up_to(ticks: AsyncIterator[Tick]):
    current = None
    async for tick in ticks:
        if current is not None:
            current.default_match_rest()
        current = TickMatcher(tick)
    return current


@define
class TickMatcher:
    """
    Defines a TickMatcher.

    A TickMatcher is responsible for matching the expected tx responses with the actual tx responses for a given tick.

    Attributes:
        tick (Tick): Tick to match.
    """

    tick: Tick

    def default_match_rest(self):
        """
        Match the rest of the tx responses with their default matcher.
        """

        for t in list(self.tick.ticked_tx_responses.keys()):
            if t == TickedTxResponsesType.INDEX_PRICE:
                self.should_process_price_no_liquidations()
            elif t == TickedTxResponsesType.PRICE_CHECKPOINT:
                self.should_mint_price_checkpoint()
            elif t == TickedTxResponsesType.ADVANCE_SETTLEMENT_EPOCH:
                self.should_advance_settlement_epoch()
            elif t == TickedTxResponsesType.ADVANCE_EPOCH:
                self.should_advance_epoch()
            elif t == TickedTxResponsesType.UPDATE_PRODUCT_LISTINGS:
                self.should_update_product_listings()
            else:
                raise AssertionError(f"Unknown TickedTxResponsesType: {t}")

    def should_process_price_no_liquidations(self):
        """
        Should submit an IndexPrice request to the operator that does not trigger a transaction, as there are no liquidations that result from this new price.
        """

        if not TickedTxResponsesType.INDEX_PRICE in self.tick.ticked_tx_responses:
            raise AssertionError("IndexPrice not included in this tick")
        expected, actual = self.tick.ticked_tx_responses.pop(
            TickedTxResponsesType.INDEX_PRICE
        )

        assert_tx_eq(expected, actual) is None

    def should_process_price_with_liquidations(self):
        """
        Should submit an IndexPrice request to the operator that triggers a Liquidation transaction.
        """

        if not TickedTxResponsesType.INDEX_PRICE in self.tick.ticked_tx_responses:
            raise AssertionError("IndexPrice not included in this tick")
        expected, actual = self.tick.ticked_tx_responses.pop(
            TickedTxResponsesType.INDEX_PRICE
        )

        assert_tx_eq(expected, actual)

    def should_mint_price_checkpoint(self):
        """
        Should submit a PriceCheckpoint request to the operator that triggers an AllPriceCheckpoints transaction.
        """

        if not TickedTxResponsesType.PRICE_CHECKPOINT in self.tick.ticked_tx_responses:
            raise AssertionError("PriceCheckpoint not included in this tick")

        expected, actual = self.tick.ticked_tx_responses.pop(
            TickedTxResponsesType.PRICE_CHECKPOINT
        )

        assert_tx_eq(expected, actual)

    def should_update_product_listings(self):
        """
        Should submit a UpdateProductListings request to the operator that triggers a TradableProductUpdate transaction.
        """

        if (
            not TickedTxResponsesType.UPDATE_PRODUCT_LISTINGS
            in self.tick.ticked_tx_responses
        ):
            raise AssertionError("UpdateProductListings not included in this tick")

        expected, actual = self.tick.ticked_tx_responses.pop(
            TickedTxResponsesType.UPDATE_PRODUCT_LISTINGS
        )
        return assert_tx_eq(expected, actual)

    def should_update_product_listings_with_additions(self):
        """
        Should submit a UpdateProductListings request to the operator that triggers a TradableProductUpdate transaction with product additions.
        """

        actual = self.should_update_product_listings()
        additions_tx = next(
            filter(
                lambda tx: isinstance(tx, TradableProductUpdate),
                actual,
            )
        )

        assert len(additions_tx.additions) > 0, f"At least one product should be added"

        return additions_tx

    def should_update_product_listings_with_removals(self):
        """
        Should submit a UpdateProductListings request to the operator that triggers a TradableProductUpdate transaction with product removals.
        """

        actual = self.should_update_product_listings()
        removal_tx = next(
            filter(
                lambda tx: isinstance(tx, TradableProductUpdate),
                actual,
            )
        )

        assert len(removal_tx.removals) > 0, f"At least one product should be removed"

        return removal_tx

    def should_advance_settlement_epoch(self):
        """
        Should submit an AdvanceSettlementEpoch request to the operator that triggers PnlRealization, Funding, and/or FuturesExpiry transactions.
        """

        if (
            not TickedTxResponsesType.ADVANCE_SETTLEMENT_EPOCH
            in self.tick.ticked_tx_responses
        ):
            raise AssertionError("AdvanceSettlementEpoch not included in this tick")

        expected, actual = self.tick.ticked_tx_responses.pop(
            TickedTxResponsesType.ADVANCE_SETTLEMENT_EPOCH
        )

        return assert_tx_eq(expected, actual)

    def should_advance_settlement_epoch_with_pnl_realization(self, negative=False):
        """
        Should submit an AdvanceSettlementEpoch request to the operator that triggers a PnlRealization transaction.
        """

        actual = self.should_advance_settlement_epoch()

        if negative:
            assert not any(
                isinstance(tx, PnlRealization) for tx in actual
            ), "PnlRealization transaction should not be present"
            return

        pnl_realization_tx = next(
            filter(
                lambda tx: isinstance(tx, PnlRealization),
                actual,
            )
        )

        return pnl_realization_tx

    def should_advance_settlement_epoch_with_trade_mining(self, negative=False):
        """
        Should submit an AdvanceSettlementEpoch request to the operator that triggers a TradeMining transaction.
        """

        actual = self.should_advance_settlement_epoch()

        if negative:
            assert not any(
                isinstance(tx, TradeMining) for tx in actual
            ), "TradeMining transaction should not be present"
            return

        trade_mining_tx = next(
            filter(
                lambda tx: isinstance(tx, TradeMining),
                actual,
            )
        )

        return trade_mining_tx

    def should_advance_settlement_epoch_with_funding(self, negative=False):
        """
        Should submit an AdvanceSettlementEpoch request to the operator that triggers a Funding transaction.
        """

        actual = self.should_advance_settlement_epoch()

        if negative:
            assert not any(
                isinstance(tx, Funding) for tx in actual
            ), "Funding transaction should not be present"
            return

        funding_tx = next(
            filter(
                lambda tx: isinstance(tx, Funding),
                actual,
            )
        )

        return funding_tx

    def should_advance_settlement_epoch_with_futures_expiry(self, negative=False):
        """
        Should submit an AdvanceSettlementEpoch request to the operator that triggers PnlRealization and FuturesExpiry transactions.
        """

        actual = self.should_advance_settlement_epoch()

        if negative:
            assert not any(
                isinstance(tx, FuturesExpiry) for tx in actual
            ), "FuturesExpiry transaction should not be present"
            return

        pnl_realization_tx = next(
            filter(
                lambda tx: isinstance(tx, PnlRealization),
                actual,
            )
        )

        futures_expiry_tx = next(
            filter(
                lambda tx: isinstance(tx, FuturesExpiry),
                actual,
            )
        )

        return pnl_realization_tx, futures_expiry_tx

    def should_advance_epoch(self):
        """
        Should submit an AdvanceEpoch request to the operator.
        """

        if not TickedTxResponsesType.ADVANCE_EPOCH in self.tick.ticked_tx_responses:
            raise AssertionError("AdvanceEpoch not included in this tick")

        expected, actual = self.tick.ticked_tx_responses.pop(
            TickedTxResponsesType.ADVANCE_EPOCH
        )

        assert_tx_eq(expected, actual)
