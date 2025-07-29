import copy
import logging
from collections import defaultdict
from typing import Optional

from ddx.common.item_utils import update_avail_collateral
from ddx.common.logging import local_logger
from ddx.common.transactions.all_price_checkpoints import AllPriceCheckpoints
from ddx.common.transactions.cancel import Cancel
from ddx.common.transactions.inner.adl_outcome import AdlOutcome
from ddx.common.transactions.inner.liquidated_position import LiquidatedPosition
from ddx.common.transactions.inner.liquidation_entry import LiquidationEntry
from ddx.common.transactions.liquidation import Liquidation
from ddx.common.transactions.price_checkpoint import PriceCheckpoint
from ddx._rust.common import ProductSymbol, TokenSymbol
from ddx._rust.common.accounting import MarkPriceMetadata
from ddx._rust.common.enums import OrderSide, PositionSide, PriceDirection
from ddx._rust.common.requests import IndexPrice, MintPriceCheckpoint
from ddx._rust.common.state import BookOrder, Position
from ddx._rust.common.state.keys import (BookOrderKey, InsuranceFundKey,
                                          PositionKey, StrategyKey)
from ddx._rust.decimal import Decimal
from sortedcontainers import SortedList
from tests.harness.execution.matching import MatchingMixin
from tests.harness.market_aware_account import MarketAwareAccount

from .utils import log_success

logger = local_logger(__name__)

EMA_MULTIPLIER = Decimal("0.0645161290322580645161290323")


class LiquidationMixin(MatchingMixin):
    def last_price(self, symbol: ProductSymbol) -> Optional[PriceCheckpoint]:
        return self.products[symbol].rolling_price

    @log_success(MintPriceCheckpoint)
    def mint_price_checkpoint(self) -> Optional[AllPriceCheckpoints]:
        price_checkpoints = self.record_price_checkpoints(
            {
                symbol: product.rolling_price
                for symbol, product in self.products.items()
                if product.rolling_price is not None
            }
        )
        logger.info(f"Recorded price checkpoints {price_checkpoints}")
        if not price_checkpoints:
            return None
        return AllPriceCheckpoints(
            list(price_checkpoints.values()),
        )

    def find_underwater_strategies(
        self,
        symbol: ProductSymbol,
        direction: Optional[PriceDirection],
    ) -> SortedList[StrategyKey]:
        res = SortedList()
        for sk, strategy in self.smt.all_strategies():
            acc = MarketAwareAccount(strategy, self.positions_for_strategy(sk))
            if symbol not in acc.positions:
                continue
            logger.info(f"Assessing solvency of strategy {sk} for {symbol}")
            pos = acc.positions[symbol][0]
            if (
                direction is None
                or (
                    pos.side == PositionSide.Long
                    and direction == PriceDirection.Down
                    or pos.side == PositionSide.Short
                    and direction == PriceDirection.Up
                )
            ) and acc.assess_solvency() == 0:
                logger.info(f"Underwater!")
                res.add(sk)
        return res

    @log_success(IndexPrice)
    def process_price(
        self, index_price: IndexPrice
    ) -> (Optional[AllPriceCheckpoints], Optional[Liquidation]):
        logger.info(f"Processing index price {index_price}")
        symbol = index_price.symbol
        index_price_hash = index_price.hash()

        last_price = self.last_price(symbol)

        fair_price = (
            mid_px
            if symbol in self.products
            and (mid_px := self.products[symbol].order_book.mid_px) is not None
            else index_price.price
        )

        premium = fair_price - index_price.price

        if (
            (parameters := self.products[symbol].tradable_product.parameters)
            is not None
            and (quarter := parameters.futures_quarter()) is not None
            and (
                expiry_tick := self.store.time_value
                + (
                    quarter.expiry_date_after(self.store.timestamp)
                    - self.store.timestamp
                ).total_seconds()
            )
            > self.epoch_params.expiry_price_leaves_duration
            and self.store.time_value
            >= expiry_tick - self.epoch_params.expiry_price_leaves_duration
        ):
            accum, count = (
                (Decimal("0"), 0)
                if last_price.mark_price_metadata.ema() is not None
                else (
                    tuple(
                        a + b
                        for a, b in zip(
                            last_price.mark_price_metadata.average(),
                            (last_price.index_price, 1),
                        )
                    )
                )
            )
            mark_price_metadata = MarkPriceMetadata.Average(
                accum.recorded_amount(), count
            )
            logger.info(
                f"Recording rolling price with running average {mark_price_metadata} and index price hash {index_price_hash}"
            )
        else:
            mark_price_metadata = MarkPriceMetadata.Ema(
                (
                    (premium - last_price.mark_price_metadata.ema()) * EMA_MULTIPLIER
                    + last_price.mark_price_metadata.ema()
                ).recorded_amount()
                if last_price is not None
                else Decimal("0")
            )
            logger.info(
                f"Recording rolling price with ema {mark_price_metadata} and index price hash {index_price_hash}"
            )
        self.products[symbol].rolling_price = PriceCheckpoint(
            symbol,
            mark_price_metadata,
            index_price_hash,
            index_price.price,
            (
                (
                    price_checkpoint.ordinal
                    if symbol in self.products
                    and (price_checkpoint := self.products[symbol].price_checkpoint)
                    is not None
                    else 0
                )
                + 1
                if (
                    (price := self.products[symbol].rolling_price) is not None
                    and not price.is_void()
                )
                # This was inconsistently implemented/tested in the Rust code (sometimes 0 was used, sometimes 1). I formalized it at 0.
                else 0
            ),
            self.store.time_value,
        )
        logger.info(
            f"Recorded rolling price {self.products[symbol].rolling_price} with mark price {self.products[symbol].rolling_price.mark_price}"
        )

        direction = (
            PriceDirection.Unknown
            if last_price is None
            else (
                PriceDirection.Up
                if self.products[symbol].rolling_price.mark_price
                > last_price.mark_price
                else PriceDirection.Down
            )
        )

        logger.info("Checking for underwater strategies...")
        underwater_strategies = self.find_underwater_strategies(symbol, direction)
        if not underwater_strategies:
            logger.info("None!")
            return
        triggered_symbols_tracker = set()
        liquidations = self.liquidate(
            underwater_strategies,
            triggered_symbols_tracker,
            self.store.time_value,
        )
        all_price_checkpoints = None
        if triggered_symbols_tracker:
            price_checkpoints = self.record_price_checkpoints(
                {
                    symbol: self.products[symbol].rolling_price
                    for symbol in triggered_symbols_tracker
                }
            )
            logger.info(f"Recorded {len(price_checkpoints)} price checkpoints")
            all_price_checkpoints = AllPriceCheckpoints(
                list(price_checkpoints.values()),
            )
        return (
            all_price_checkpoints,
            Liquidation(liquidations) if liquidations else None,
        )

    def freeze_strategy(self, trader_address: str, strategy_id_hash: str):
        strategy_key: StrategyKey = StrategyKey(trader_address, strategy_id_hash)
        strategy = self.smt.strategy(strategy_key)
        strategy.frozen = True
        logger.info(f"Freezing strategy {strategy_key}")
        self.smt.store_strategy(strategy_key, strategy)

    def find_open_orders_by_strategy(self, trader_address: str, strategy_id_hash: str):
        order_keys = []
        for symbol in self.products:
            two_sided_book = [
                self.products[symbol].order_book.ask_keys,
                self.products[symbol].order_book.bid_keys,
            ]
            for sided_book in two_sided_book:
                for _, maker_orders in sided_book.items():
                    for order_key in maker_orders:
                        book_order = self.products[symbol].order_book.book_orders[
                            order_key
                        ]
                        if (
                            book_order.trader_address == trader_address
                            and book_order.strategy_id_hash == strategy_id_hash
                        ):
                            order_keys.append(order_key)

        logger.info(
            f"Found {len(order_keys)} open orders for trader address {trader_address} strategy id hash {strategy_id_hash}"
        )
        return [
            (
                order_key,
                self.products[order_key.symbol].order_book.book_orders[order_key],
            )
            for order_key in order_keys
        ]

    def liquidate(
        self,
        underwater_strategies: list[StrategyKey],
        triggered_symbols_tracker: set[str],
        time_value: int,
    ):
        logger.info(f"Beginning liquidations!")
        for sk in underwater_strategies:
            self.freeze_strategy(sk.trader_address, sk.strategy_id_hash)
        cancels_by_strategy = {}
        for sk in underwater_strategies:
            cancels = []
            logger.info(f"Finding open orders for strategy {sk}")
            for book_order_key, book_order in self.find_open_orders_by_strategy(
                sk.trader_address, sk.strategy_id_hash
            ):
                self.store_book_order(book_order_key, None)
                cancels.append(
                    Cancel(
                        book_order_key.symbol,
                        book_order_key.order_hash,
                        book_order.amount,
                    )
                )
            cancels_by_strategy[sk] = cancels
        liquidations = []
        logger.info(f"Liquidating strategies")
        for sk in underwater_strategies:
            liquidation = self.liquidate_strategy(
                sk, triggered_symbols_tracker, time_value
            )
            liquidation.canceled_orders = cancels_by_strategy.pop(sk)
            liquidations.append(liquidation)
        logger.info(f"We're done with liquidations!")
        return liquidations

    def liquidate_strategy(
        self,
        strategy_key: StrategyKey,
        triggered_symbols_tracker: set[str],
        time_value: int,
    ):
        logger.info(f"Liquidating strategy {strategy_key}")
        liq_strategy = self.smt.strategy(strategy_key)
        positions = copy.deepcopy(
            MarketAwareAccount(
                liq_strategy, self.positions_for_strategy(strategy_key)
            ).sorted_positions_by_unrealized_pnl()
        )
        liquidated_positions = []
        while positions:
            liq_acc = MarketAwareAccount(
                self.smt.strategy(strategy_key),
                self.positions_for_strategy(strategy_key),
            )
            total_value = liq_acc.total_value
            symbol, (position, price) = positions.pop(0)
            liquidated_position, matching_orders = self.liquidate_position(
                symbol,
                strategy_key,
                position,
                price,
                total_value,
                triggered_symbols_tracker,
                time_value,
            )
            if self.store.is_trade_mining():
                self.apply_trade_mining_rewards(
                    liquidated_position.trade_outcomes,
                    matching_orders,
                    None,
                    time_value,
                )
            liquidated_positions.append((symbol, liquidated_position))

        # Unfreeze
        # Note: this is only relevant for liquidations for multi-collateral balances and strategies with empty positions
        if (strategy := self.smt.strategy(strategy_key)) is not None:
            strategy.frozen = False
            self.smt.store_strategy(strategy_key, strategy)

        logger.info(f"We're done liquidating strategy {strategy_key}!")
        return LiquidationEntry(
            strategy_key.trader_address,
            strategy_key.strategy_id_hash,
            [],
            liquidated_positions,
        )

    def liquidate_position(
        self,
        symbol: ProductSymbol,
        strategy_key: StrategyKey,
        liquidated_position: Position,
        price: PriceCheckpoint,
        total_value: Decimal,
        triggered_symbols_tracker: set[str],
        time_value: int,
    ):
        logger.info(
            f"Liquidating position {liquidated_position} of {price.symbol} at mark price {price.mark_price}"
        )
        triggered_symbols_tracker.add(symbol)
        amount_to_liquidate = liquidated_position.balance
        bankruptcy_price = liquidated_position.bankruptcy_price(
            price.mark_price, total_value
        )
        logger.info(f"Bankruptcy price: {bankruptcy_price}")
        (
            trade_outcomes,
            matching_orders,
            new_insurance_fund_cap,
            collateral,
        ) = self.do_liquidation_sale(
            symbol,
            strategy_key,
            liquidated_position,
            bankruptcy_price,
            triggered_symbols_tracker,
            time_value,
        )
        logger.info(f"Collateral after liquidation sales: {collateral}")
        adl_outcomes = []
        if liquidated_position.balance > Decimal("0"):
            logger.info(f"Balance of {liquidated_position.balance} remains, doing ADL")
            adl_outcomes = self.do_adl(
                strategy_key,
                symbol,
                liquidated_position,
                bankruptcy_price,
                collateral,
            )

        # Update position in SMT
        logger.info(f"Updating position to {liquidated_position}")
        self.smt.store_position(
            PositionKey(
                strategy_key.trader_address, strategy_key.strategy_id_hash, symbol
            ),
            liquidated_position,
        )

        logger.info(f"We're done liquidating position {liquidated_position}!")
        return (
            LiquidatedPosition(
                amount_to_liquidate,
                trade_outcomes,
                adl_outcomes,
                new_insurance_fund_cap,
                -1,
            ),
            matching_orders,
        )

    def do_liquidation_sale(
        self,
        symbol: ProductSymbol,
        strategy_key: StrategyKey,
        liquidated_position: Position,
        bankruptcy_price: Decimal,
        triggered_symbols_tracker: set[str],
        time_value: int,
    ):
        logger.info(f"Selling {liquidated_position.side} position to open market")
        min_order_size = self.market_specs[
            self.products[symbol].tradable_product.specs
        ].min_order_size

        strategy = self.smt.strategy(strategy_key)
        remaining_collateral = strategy.avail_collateral[TokenSymbol.USDC]

        insurance_fund_key: InsuranceFundKey = InsuranceFundKey()
        insurance_fund = self.smt.insurance_fund(insurance_fund_key)
        insurance_fund_cap = insurance_fund[TokenSymbol.USDC]

        trade_outcomes = []
        orders = []
        mark_price = self.last_price(symbol).mark_price
        taker_side = (
            OrderSide.Bid
            if liquidated_position.side == PositionSide.Short
            else OrderSide.Ask
        )
        logger.info(
            f"Finding open {liquidated_position.side} (maker) orders on the book (virtual taker side is {taker_side})"
        )
        logger.info(
            f"Note: to exclude possibility of self match, we filter out the liquidated trader's orders from the book when matching"
        )
        while True:
            matches = self.filter_matching_orders(
                symbol,
                taker_side,
                mark_price,
                None,
                liquidated_position.balance,
                None,
                self.market_specs[
                    self.products[symbol].tradable_product.specs
                ].max_taker_price_deviation,
                triggered_symbols_tracker,
            )[0]
            if not matches:
                logger.info("No more matching orders")
                break
            # orders.extend(matches)
            for book_order_key, order in matches:
                price_delta = order.price - bankruptcy_price
                if liquidated_position.side == PositionSide.Short:
                    price_delta = -price_delta
                possible_fill_amount = min(order.amount, liquidated_position.balance)
                fill_amount = (
                    min(possible_fill_amount, insurance_fund_cap / abs(price_delta))
                    if price_delta < 0
                    else possible_fill_amount
                )
                fill_amount -= fill_amount % min_order_size
                if fill_amount == Decimal("0"):
                    logger.info(
                        f"We're done! No more remaining balance on this position or insurance fund is depleted."
                    )
                    break
                orders.append((book_order_key, order))
                maybe_fill, maybe_cancel, _ = self.take_order(
                    symbol,
                    mark_price,
                    BookOrder(
                        taker_side,
                        fill_amount,
                        Decimal("0"),
                        "0x000000000000000000000000000000000000000000",
                        "0x00000000",
                        0,
                        time_value,
                    ),
                    None,
                    book_order_key,
                    order,
                    triggered_symbols_tracker,
                )
                if maybe_fill is not None:
                    old_insurance_fund_cap = insurance_fund_cap
                    insurance_fund_delta = price_delta * maybe_fill.amount
                    insurance_fund_cap += insurance_fund_delta
                    remaining_collateral += (
                        liquidated_position.avg_pnl(bankruptcy_price)
                        * maybe_fill.amount
                    )
                    logger.info(
                        f"Filling {maybe_fill.amount} for this order. Liquidated trader's collateral is now {remaining_collateral}\n\told insurance fund: {old_insurance_fund_cap}\n\tnew insurance fund: {insurance_fund_cap}\n\tdelta: {insurance_fund_delta}"
                    )
                    liquidated_position.balance -= maybe_fill.amount
                    trade_outcomes.append(maybe_fill)
                if maybe_cancel is not None:
                    logger.info(f"Canceling maker order")
                    trade_outcomes.append(maybe_cancel)
            else:
                continue
            break

        # Update strategy in SMT
        logger.info(f"Updating strategy's collateral to {remaining_collateral}")
        update_avail_collateral(
            strategy,
            TokenSymbol.USDC,
            remaining_collateral,
        )
        self.smt.store_strategy(strategy_key, strategy)

        # Update insurance fund in SMT
        insurance_fund_cap = insurance_fund_cap.recorded_amount()
        logger.info(f"Updating insurance fund cap to {insurance_fund_cap}")
        insurance_fund[TokenSymbol.USDC] = insurance_fund_cap
        self.smt.store_insurance_fund(insurance_fund_key, insurance_fund)

        return (trade_outcomes, orders, insurance_fund_cap, remaining_collateral)

    def do_adl(
        self,
        strategy_key: StrategyKey,
        symbol: ProductSymbol,
        liquidated_position: Position,
        bankruptcy_price: Decimal,
        remaining_collateral: Decimal,
    ):
        logger.info(
            f"Performing ADL for position {liquidated_position} at bankruptcy price {bankruptcy_price}"
        )
        positions_by_symbol = {
            PositionKey(
                strategy_key.trader_address, strategy_key.strategy_id_hash, symbol
            ): positions[symbol][0]
            for strategy_key, strategy in self.smt.all_strategies()
            if symbol
            in (
                positions := MarketAwareAccount(
                    strategy, self.positions_for_strategy(strategy_key)
                ).positions
            )
        }
        matching_candidates = [
            (pk, pos)
            for pk, pos in positions_by_symbol.items()
            if pos.side != liquidated_position.side
            and pos.side != PositionSide.Empty
            and not (
                pk.trader_address == strategy_key.trader_address
                and pk.strategy_id_hash == strategy_key.strategy_id_hash
            )
        ]
        logger.info(
            f"Found {len(matching_candidates)} matching candidate positions, sorting in descending order of unrealized pnl"
        )
        matching_candidates.sort(
            key=lambda candidate: (
                -candidate[1].unrealized_pnl(bankruptcy_price),
                candidate[0],
            )
        )
        adl_outcomes = []
        for pk, pos in matching_candidates:
            if liquidated_position.balance == Decimal("0"):
                logger.info("Balance is zero, we're done ADLing")
                break
            match_token_amount = min(liquidated_position.balance, pos.balance)
            liquidated_position.balance -= match_token_amount
            pos.balance -= match_token_amount
            self.smt.store_position(pk, pos)
            liquidated_trader_realized_pnl = (
                liquidated_position.avg_pnl(bankruptcy_price) * match_token_amount
            )
            remaining_collateral += liquidated_trader_realized_pnl

            adl_trader_realized_pnl = pos.avg_pnl(bankruptcy_price) * match_token_amount
            adl_trader_strategy = self.smt.strategy(
                pk.as_strategy_key(),
            )
            old_collateral = adl_trader_strategy.avail_collateral[TokenSymbol.USDC]
            new_collateral = old_collateral + adl_trader_realized_pnl
            if new_collateral < 0:
                raise Exception("free collateral is negative after adl")
            update_avail_collateral(
                adl_trader_strategy,
                TokenSymbol.USDC,
                new_collateral,
            )
            logger.info(
                f"ADLing {match_token_amount}. Liquidated trader's collateral is now {remaining_collateral}\n\told adl'd trader's balance: {old_collateral}\n\tnew adl'd trader's balance: {new_collateral}\n\trealized pnl: {adl_trader_realized_pnl}"
            )
            self.smt.store_strategy(pk.as_strategy_key(), adl_trader_strategy)
            adl_outcomes.append(
                AdlOutcome(
                    pk.trader_address,
                    pk.strategy_id_hash,
                )
            )

        logger.info(
            f"Updating liquidated strategy's collateral to {remaining_collateral}"
        )
        strategy = self.smt.strategy(strategy_key)
        strategy.avail_collateral[TokenSymbol.USDC] = remaining_collateral
        update_avail_collateral(
            strategy,
            TokenSymbol.USDC,
            remaining_collateral,
        )
        self.smt.store_strategy(strategy_key, strategy)

        logger.info(f"Totalled {len(adl_outcomes)} ADL outcomes")
        return adl_outcomes
