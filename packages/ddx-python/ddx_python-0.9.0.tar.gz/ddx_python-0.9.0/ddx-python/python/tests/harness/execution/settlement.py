import logging
from collections import defaultdict
from typing import Iterable, Iterator, Optional

from ddx.common.item_utils import update_avail_collateral
from ddx.common.logging import local_logger
from ddx.common.transactions.advance_settlement_epoch import \
    AdvanceSettlementEpoch as AdvanceSettlementEpochTx
from ddx.common.transactions.all_price_checkpoints import AllPriceCheckpoints
from ddx.common.transactions.funding import Funding, get_funding_rate
from ddx.common.transactions.futures_expiry import FuturesExpiry
from ddx.common.transactions.inner.outcome import Outcome
from ddx.common.transactions.liquidation import Liquidation
from ddx.common.transactions.pnl_realization import PnlRealization
from ddx.common.transactions.trade_mining import TradeMining
from ddx._rust.common import ProductSymbol, TokenSymbol
from ddx._rust.common.enums import OrderSide, PositionSide, TradeSide
from ddx._rust.common.requests import AdvanceSettlementEpoch, SettlementAction
from ddx._rust.common.state.keys import PositionKey, StrategyKey
from ddx._rust.decimal import Decimal
from tests.harness.market_aware_account import MarketAwareAccount

from .utils import log_success

logger = local_logger(__name__)


class SettlementMixin:
    def find_open_orders_by_symbols(self, symbols: set[ProductSymbol]):
        order_keys = []
        for symbol in self.products:
            if symbol not in symbols:
                continue
            two_sided_book = [
                self.products[symbol].order_book.ask_keys,
                self.products[symbol].order_book.bid_keys,
            ]
            for sided_book in two_sided_book:
                for _, maker_orders in sided_book.items():
                    order_keys.extend(order_key for order_key in maker_orders)

        logger.info(f"Found {len(order_keys)} open orders for symbols {symbols}")
        return [
            (
                order_key,
                self.products[order_key.symbol].order_book.book_orders[order_key],
            )
            for order_key in order_keys
        ]

    def filter_underwater(
        self,
        strategies: Iterable[StrategyKey],
    ) -> Iterator[StrategyKey]:
        for sk in strategies:
            acc = MarketAwareAccount(
                self.smt.strategy(sk), self.positions_for_strategy(sk)
            )
            logger.info(f"Assessing solvency of strategy {sk}")
            if acc.assess_solvency() == 0:
                logger.info(f"Underwater!")
                yield sk

    @log_success(AdvanceSettlementEpoch)
    def advance_settlement_epoch(self, request: AdvanceSettlementEpoch) -> (
        Optional[AllPriceCheckpoints],
        Optional[TradeMining],
        Optional[PnlRealization],
        Optional[FuturesExpiry],
        Optional[Funding],
        AdvanceSettlementEpochTx,
    ):
        logger.info(f"Settlement actions: {request.actions}")

        all_price_checkpoints = None
        rolling_prices = {
            symbol: product.rolling_price
            for symbol, product in self.products.items()
            if product.rolling_price is not None
        }
        logger.info(f"Creating price checkpoints for rolling prices {rolling_prices}")
        price_checkpoints = self.record_price_checkpoints(rolling_prices)
        if price_checkpoints:
            all_price_checkpoints = AllPriceCheckpoints(
                list(price_checkpoints.values())
            )

        trade_mining = None
        if (
            self.store.is_trade_mining()
            and SettlementAction.TradeMining in request.actions
        ):
            logger.info(f"Recording trade mining this settlement epoch")
            trade_mining_ = self.distribute_trade_mining_rewards(
                request.epoch_id,
                self.trade_mining_params.trade_mining_reward_per_epoch,
                self.trade_mining_params.trade_mining_maker_reward_percentage,
                self.trade_mining_params.trade_mining_taker_reward_percentage,
            )
            if trade_mining_.ddx_distributed > Decimal("0"):
                trade_mining = trade_mining_
            logger.info(f"Done with trade mining")

        pnl_realization = None
        if SettlementAction.PnlRealization in request.actions:
            logger.info(f"Pnl realization this settlement epoch")
            pnl_realization = PnlRealization(
                request.epoch_id,
                request.time.value,
            )
            logger.info(f"Done with pnl realization")

        funding = None
        funding_rates = {}
        funding_liquidations = []
        total_funding_payments = defaultdict(Decimal)
        if SettlementAction.FundingDistribution in request.actions:
            logger.info(f"Funding this settlement epoch")
            for symbol, product in self.products.items():
                if product.rolling_price is None:
                    continue
                # extra price leaves are passed in rather than modifying the smt directly
                # when recording price checkpoints to ensure that only the auditor can
                # modify the smt for consistent smt state between requests
                if (
                    funding_rate := get_funding_rate(
                        self.smt, self.epoch_params.funding_period, symbol
                    )
                ) is not None:
                    funding_rates[symbol] = funding_rate
                    logger.info(f"Funding rate for {symbol}: {funding_rate}")

        # expiry settlements happen sequentially before funding but after pnl realization
        futures_expiry = None
        expiry_quarters = [
            quarter
            for action in request.actions
            if (quarter := action.futures_quarter()) is not None
        ]
        assert len(expiry_quarters) <= 1, "At most one expiry should occur"
        expiry_quarter = expiry_quarters[0] if expiry_quarters else None
        expiry_symbols = {
            symbol
            for symbol, product in self.products.items()
            if (parameters := product.tradable_product.parameters) is not None
            and (quarter := parameters.futures_quarter()) is not None
            and quarter == expiry_quarter
        }
        if expiry_symbols:
            logger.info(f"Expiring {expiry_quarter}-futures this settlement epoch")
            logger.info(f"Closing all open orders for {expiry_symbols}")
            for book_order_key, book_order in self.find_open_orders_by_symbols(
                expiry_symbols
            ):
                self.store_book_order(book_order_key, None)
        for sk, strategy in self.smt.all_strategies():
            logger.info(f"For strategy {sk}:")
            acc = MarketAwareAccount(strategy, self.positions_for_strategy(sk))
            funding_payments = {}
            strategy_dirty = False
            for symbol, (position, price) in acc.positions.items():
                logger.info(f"For {symbol} position and mark price {price.mark_price}:")
                if position.side == PositionSide.Empty:
                    logger.warn("Empty position, skipping")
                    continue

                if symbol in funding_rates:
                    funding_payments[symbol] = (
                        funding_rates[symbol]
                        * position.balance
                        * price.mark_price
                        * (-1 if position.side == PositionSide.Long else 1)
                    )
                    logger.info(
                        f"Calculated funding payment for {symbol}: {funding_payments[symbol]}"
                    )

                if SettlementAction.PnlRealization in request.actions:
                    balance = strategy.avail_collateral[TokenSymbol.USDC]
                    update_avail_collateral(
                        strategy,
                        TokenSymbol.USDC,
                        strategy.avail_collateral[TokenSymbol.USDC]
                        + position.unrealized_pnl(price.mark_price),
                    )
                    new_balance = strategy.avail_collateral[TokenSymbol.USDC]
                    amount = new_balance - balance

                    if amount != Decimal("0") or symbol in expiry_symbols:
                        position.avg_entry_price = price.mark_price.recorded_amount()

                        if symbol in expiry_symbols:
                            logger.info(f"Closing futures position for {symbol}")
                            position, _ = position.decrease(
                                position.avg_entry_price, position.balance
                            )
                            logger.info(f"Closed position to be stored: {position}")

                        self.smt.store_position(
                            PositionKey(sk.trader_address, sk.strategy_id_hash, symbol),
                            position,
                        )
                        strategy_dirty = True
                    logger.info(
                        f"Calculated realized pnl:\n\told balance: {balance}\n\tnew balance: {new_balance}\n\tpnl realized: {amount}"
                    )

            if funding_payments:
                balance = strategy.avail_collateral[TokenSymbol.USDC]
                update_avail_collateral(
                    strategy,
                    TokenSymbol.USDC,
                    strategy.avail_collateral[TokenSymbol.USDC]
                    + sum(funding_payments.values()),
                )
                new_balance = strategy.avail_collateral[TokenSymbol.USDC]
                if new_balance != balance:
                    strategy_dirty = True
                    for symbol, payment in funding_payments.items():
                        total_funding_payments[symbol] += payment
                logger.info(
                    f"Applied funding payment:\n\told balance: {balance}\n\tnew balance: {new_balance}\n\tfunding: {new_balance - balance}"
                )

            if strategy_dirty:
                self.smt.store_strategy(sk, strategy)

        if expiry_symbols:
            futures_expiry = FuturesExpiry(
                request.epoch_id,
                expiry_quarter,
                request.time.value,
            )
            logger.info(f"Done with expiring {expiry_quarter}-futures")

        if total_funding_payments:
            logger.info(
                f"Processing market impact of funding, found imbalance of {sum(total_funding_payments.values())}"
            )
            logger.info("Checking for underwater strategies...")
            other_symbols = set()
            for symbol in funding_rates.keys():
                underwater = self.find_underwater_strategies(symbol, None)
                if not underwater:
                    logger.info("None!")
                    continue
                funding_liquidations.extend(
                    self.liquidate(underwater, other_symbols, self.store.time_value)
                )
        if SettlementAction.FundingDistribution in request.actions:
            funding = Funding(
                request.epoch_id,
                Liquidation(
                    funding_liquidations,
                ),
                request.time.value,
            )
            logger.info(f"Done with funding")

        # Drain price checkpoints
        # Find most recent price for each symbol
        carryover_price_keys = {}
        for price_key, price in self.smt.all_prices():
            if (
                price_key.symbol not in carryover_price_keys
                or price.ordinal
                > self.smt.price(carryover_price_keys[price_key.symbol]).ordinal
            ):
                carryover_price_keys[price_key.symbol] = price_key

        for price_key, _ in self.smt.all_prices():
            if price_key != carryover_price_keys[price_key.symbol]:
                self.smt.store_price(price_key, None)

        return (
            all_price_checkpoints,
            trade_mining,
            pnl_realization,
            futures_expiry,
            funding,
            AdvanceSettlementEpochTx(),
        )
