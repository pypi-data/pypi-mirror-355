import copy
import logging
from enum import Enum
from typing import Optional, Union

from ddx.common.fill_context import (MAX_DDX_PRICE_CHECKPOINT_AGE_IN_TICKS,
                                 FillContext)
from ddx.common.logging import local_logger
from ddx.common.transactions.all_price_checkpoints import AllPriceCheckpoints
from ddx.common.transactions.cancel import Cancel
from ddx.common.transactions.cancel_all import CancelAll
from ddx.common.transactions.complete_fill import CompleteFill
from ddx.common.transactions.inner.fill import Fill
from ddx.common.transactions.inner.liquidation_fill import LiquidationFill
from ddx.common.transactions.inner.outcome import Outcome
from ddx.common.transactions.inner.trade_fill import TradeFill
from ddx.common.transactions.partial_fill import PartialFill
from ddx.common.transactions.post import Post
from ddx.common.transactions.post_order import PostOrder
from ddx.common.transactions.price_checkpoint import PriceCheckpoint
from ddx._rust.common import ProductSymbol, TokenSymbol
from ddx._rust.common.enums import OrderSide, OrderType, TradeSide
from ddx._rust.common.requests.intents import (CancelAllIntent,
                                                CancelOrderIntent,
                                                ModifyOrderIntent, OrderIntent)
from ddx._rust.common.state import BookOrder, Position, Strategy
from ddx._rust.common.state.keys import (BookOrderKey, EpochMetadataKey,
                                          InsuranceFundKey, StrategyKey,
                                          TraderKey)
from ddx._rust.decimal import Decimal
from tests.harness.market_aware_account import MarketAwareAccount

from .utils import log_success

logger = local_logger(__name__)

POST_ONLY_VIOLATION = "PostOnlyViolation"


class PartialFillPolicy(str, Enum):
    CancelRemainingAmount = "CancelRemainingAmount"
    PostRemainingAmount = "PostRemainingAmount"


class MatchingMixin:
    @log_success(CancelOrderIntent)
    def cancel(
        self,
        cancelable_intent: CancelOrderIntent | ModifyOrderIntent,
    ) -> Optional[Cancel]:
        book_order_key: BookOrderKey = BookOrderKey(
            cancelable_intent.symbol, cancelable_intent.order_hash
        )
        book_order = self.smt.book_order(book_order_key)
        if book_order is None:
            return None
        self.store_book_order(book_order_key, None)

        return Cancel(
            cancelable_intent.symbol,
            cancelable_intent.order_hash,
            book_order.amount,
        )

    @log_success(CancelAllIntent)
    def cancel_all(
        self,
        cancel_all_intent: CancelAllIntent,
    ) -> CancelAll:
        _, trader_address = cancel_all_intent.recover_signer()
        strategy_id_hash = StrategyKey.generate_strategy_id_hash(
            cancel_all_intent.strategy
        )
        cancel_keys = [
            book_order_key
            for book_order_key, book_order in self.products[
                cancel_all_intent.symbol
            ].order_book.book_orders.items()
            if book_order.trader_address == trader_address
            and book_order.strategy_id_hash == strategy_id_hash
        ]
        for book_order_key in cancel_keys:
            self.store_book_order(book_order_key, None)
        return CancelAll(
            cancel_all_intent.symbol,
            trader_address,
            strategy_id_hash,
        )

    def last_price_with_max_age(
        self, symbol: ProductSymbol, max_age: int
    ) -> Optional[PriceCheckpoint]:
        if (
            symbol in self.products
            and (last_price_checkpoint := self.products[symbol].price_checkpoint)
            is not None
            and not last_price_checkpoint.is_void()
            and self.store.time_value - last_price_checkpoint.time_value <= max_age
        ):
            return last_price_checkpoint
        return None

    def filter_matching_orders(
        self,
        symbol: ProductSymbol,
        taker_side: OrderSide,
        mark_price: Decimal,
        limit_price: Optional[Decimal],
        remaining_amount: Decimal,
        taker_strategy_key: Optional[StrategyKey],
        max_taker_price_deviation: Decimal,
        triggered_symbols_tracker: set,
    ):
        if remaining_amount == Decimal("0") or symbol not in self.products:
            logger.info("Found no matching orders")
            return [], False, None

        sided_book = (
            self.products[symbol].order_book.ask_keys
            if taker_side == OrderSide.Bid
            else self.products[symbol].order_book.bid_keys
        )

        eligible_orders: list[BookOrderKey] = []
        for maker_price, maker_orders in sorted(
            sided_book.items(),
            key=lambda x: x[0],
            reverse=taker_side == OrderSide.Ask,
        ):
            if limit_price is not None:
                is_tighter_than_or_equal = (
                    limit_price >= maker_price
                    if taker_side == OrderSide.Bid
                    else limit_price <= maker_price
                )
                if not is_tighter_than_or_equal:
                    break
            elif max_taker_price_deviation > Decimal("0"):
                mtpd_price = (
                    mark_price * (Decimal("1") + max_taker_price_deviation)
                    if taker_side == OrderSide.Bid
                    else mark_price * (Decimal("1") - max_taker_price_deviation)
                )
                logger.info(f"Max taker price deviation price: {mtpd_price}")
                is_tighter_than_or_equal = (
                    mtpd_price >= maker_price
                    if taker_side == OrderSide.Bid
                    else mtpd_price <= maker_price
                )
                if not is_tighter_than_or_equal:
                    logger.info(
                        f"Max taker price deviation safety guard triggered, checkpointing price"
                    )
                    triggered_symbols_tracker.add(symbol)
                    break

            eligible_orders.extend(maker_orders)

        logger.info(f"Found {len(eligible_orders)} eligible orders")

        found_self_match: Optional[bool] = False
        matches: list[tuple[BookOrderKey, BookOrder]] = []
        maybe_partial_fill_policy: Optional[PartialFillPolicy] = None

        for maker_book_order_key in eligible_orders:
            if remaining_amount == Decimal("0"):
                break

            maker_book_order = self.products[symbol].order_book.book_orders[
                maker_book_order_key
            ]
            maker_strategy_key = StrategyKey(
                maker_book_order.trader_address,
                maker_book_order.strategy_id_hash,
            )

            if (
                taker_strategy_key is not None
                and taker_strategy_key == maker_strategy_key
            ):
                logger.info(f"Found a self match! Canceling remaining amount")
                found_self_match = True
                remaining_amount = Decimal("0")
                maybe_partial_fill_policy = PartialFillPolicy.CancelRemainingAmount
                continue

            remaining_amount = max(
                Decimal("0"), remaining_amount - maker_book_order.amount
            )
            matches.append((maker_book_order_key, maker_book_order))

        logger.info(f"Found {len(matches)} matching orders")

        return matches, found_self_match, maybe_partial_fill_policy

    def settle_fill_side_and_capture_outcome(
        self,
        fill: Fill,
        symbol: ProductSymbol,
        order_side: OrderSide,
        trade_side: TradeSide,
        strategy_key: StrategyKey,
    ):
        logger.info(f"Before settling {trade_side}: {fill}")

        strategy: Optional[Strategy] = self.smt.strategy(strategy_key)
        position: Optional[Position] = self.smt.position(
            strategy_key.as_position_key(symbol)
        )

        outcome = (
            fill.maker_outcome if trade_side == TradeSide.Maker else fill.taker_outcome
        )
        outcome.trader = strategy_key.trader_address
        outcome.strategy_id_hash = strategy_key.strategy_id_hash
        context = FillContext(outcome)

        position = context.apply_fill(
            position, order_side, trade_side, fill.amount, fill.price
        )
        self.smt.store_position(
            strategy_key.as_position_key(symbol),
            position,
        )

        logger.info(f"New position after fill: {position}")

        trader = self.smt.trader(TraderKey(strategy_key.trader_address))
        if trader.pay_fees_in_ddx:
            if (
                ddx_checkpoint := self.last_price_with_max_age(
                    ProductSymbol("DDXP"),
                    MAX_DDX_PRICE_CHECKPOINT_AGE_IN_TICKS,
                )
            ) is not None:
                if context.apply_ddx_fee_and_mutate_trader(
                    trader, ddx_checkpoint.index_price
                ):
                    self.smt.store_trader(
                        TraderKey(strategy_key.trader_address), trader
                    )
            else:
                raise Exception(
                    "DDX fee election enabled but no DDX price checkpoint within the max age was found"
                )

        context.realize_trade_and_mutate_strategy(strategy)

        logger.info(f"New strategy after fill: {strategy}")

        self.smt.store_strategy(
            strategy_key,
            strategy,
        )

        logger.info(f"Settled {trade_side}: {fill}")

    def take_order(
        self,
        symbol: ProductSymbol,
        mark_price: Decimal,
        taker_book_order: BookOrder,
        taker: Optional[tuple[StrategyKey, str]],
        maker_order_key: BookOrderKey,
        maker_order: BookOrder,
        triggered_symbols_tracker: set,
    ):
        min_order_size = self.market_specs[
            self.products[symbol].tradable_product.specs
        ].min_order_size

        logger.info(f"\nMaker:\n\t{maker_order}\nTaker:\n\t{taker_book_order}")
        maker_strategy_key = StrategyKey(
            maker_order.trader_address,
            maker_order.strategy_id_hash,
        )
        maker_acc = MarketAwareAccount(
            self.smt.strategy(maker_strategy_key),
            self.positions_for_strategy(maker_strategy_key),
        )
        maximum_maker_amount = maker_acc.maximum_fill_amount(
            symbol,
            Decimal("0"),
            mark_price,
            maker_order.side,
            maker_order.price,
            maker_order.amount,
            min_order_size,
        )
        logger.info(f"Max maker amount: {maximum_maker_amount}")

        taker_clamped = False
        if taker is not None:
            (taker_strategy_key, taker_order_hash) = taker
            taker_acc = MarketAwareAccount(
                self.smt.strategy(taker_strategy_key),
                self.positions_for_strategy(taker_strategy_key),
            )
            maximum_taker_amount = taker_acc.maximum_fill_amount(
                symbol,
                Decimal("0.002"),
                mark_price,
                (OrderSide.Bid if maker_order.side == OrderSide.Ask else OrderSide.Ask),
                maker_order.price,
                taker_book_order.amount,
                min_order_size,
            )
            logger.info(f"Max taker amount: {maximum_taker_amount}")

            if maximum_taker_amount < taker_book_order.amount and maximum_taker_amount <= maximum_maker_amount:
                triggered_symbols_tracker.add(symbol)
                triggered_symbols_tracker.update(taker_acc.positions.keys())
                taker_book_order.amount = maximum_taker_amount
                taker_clamped = True
        else:
            maximum_taker_amount = taker_book_order.amount

        if maximum_taker_amount == Decimal("0"):
            logger.info(f"Max taker amount is zero. Not filling")
            return (None, None, taker_clamped)

        if maximum_maker_amount == Decimal("0"):
            logger.info(f"Max maker amount is zero. Not filling and canceling maker")
            triggered_symbols_tracker.add(symbol)
            triggered_symbols_tracker.update(maker_acc.positions.keys())

            self.store_book_order(maker_order_key, None)

            return (
                None,
                Cancel(
                    symbol,
                    maker_order_key.order_hash,
                    maker_order.amount,
                ),
                taker_clamped,
            )

        (fill_amount, should_cancel_maker_order) = (
            (maximum_maker_amount, True)
            if maximum_maker_amount < maximum_taker_amount
            else (maximum_taker_amount, False)
        )

        logger.info(
            f"Filling order for {fill_amount}, cancel maker? {should_cancel_maker_order}"
        )

        taker_book_order.amount = taker_book_order.amount - fill_amount

        maybe_cancel = None

        maker_order_remaining_amount = maker_order.amount - fill_amount

        logger.info(
            f"Taker remaining: {taker_book_order.amount}, maker remaining: {maker_order_remaining_amount}"
        )

        if taker is not None:
            logger.info("Creating trade fill")
            fill = TradeFill(
                symbol,
                taker[1],
                maker_order_key.order_hash,
                maker_order_remaining_amount,
                fill_amount,
                maker_order.price,
                OrderSide.Bid if maker_order.side == OrderSide.Ask else OrderSide.Ask,
                Outcome(),
                Outcome(),
                taker_book_order.time_value,
            )
        else:
            logger.info("Creating liquidation fill")
            index_price = self.last_price(symbol)
            index_price_hash = index_price.index_price_hash
            fill = LiquidationFill(
                symbol,
                index_price_hash,
                maker_order_key.order_hash,
                maker_order_remaining_amount,
                fill_amount,
                maker_order.price,
                OrderSide.Bid if maker_order.side == OrderSide.Ask else OrderSide.Ask,
                Outcome(),
                taker_book_order.time_value,
            )

        maker_order.amount = maker_order.amount - fill_amount
        self.store_book_order(maker_order_key, maker_order)
        if maker_order.amount != Decimal("0") and should_cancel_maker_order:
            logger.info(f"Canceling maker order")
            triggered_symbols_tracker.add(symbol)
            triggered_symbols_tracker.update(maker_acc.positions.keys())

            self.store_book_order(maker_order_key, None)
            maybe_cancel = Cancel(
                symbol,
                maker_order_key.order_hash,
                maker_order.amount,
            )

        self.settle_fill_side_and_capture_outcome(
            fill,
            symbol,
            maker_order.side,
            TradeSide.Maker,
            maker_strategy_key,
        )
        logger.debug(
            f"New maker margin fraction after taking order: {MarketAwareAccount(self.smt.strategy(maker_strategy_key), self.positions_for_strategy(maker_strategy_key)).margin_fraction}"
        )

        if taker is not None:
            self.settle_fill_side_and_capture_outcome(
                fill,
                symbol,
                (OrderSide.Bid if maker_order.side == OrderSide.Ask else OrderSide.Ask),
                TradeSide.Taker,
                taker_strategy_key,
            )
            logger.debug(
                f"New taker margin fraction after taking order: {MarketAwareAccount(self.smt.strategy(taker[0]), self.positions_for_strategy(taker[0])).margin_fraction}"
            )

        self.reconcile_fees(fill)

        return fill, maybe_cancel, taker_clamped

    def reconcile_fees(self, fill: Fill):
        fees_default, fees_ddx = Decimal("0"), Decimal("0")
        if hasattr(fill, "maker_outcome"):
            if fill.maker_outcome.pay_fee_in_ddx:
                fees_ddx += fill.maker_outcome.fee
            else:
                fees_default += fill.maker_outcome.fee
        if hasattr(fill, "taker_outcome"):
            if fill.taker_outcome.pay_fee_in_ddx:
                fees_ddx += fill.taker_outcome.fee
            else:
                fees_default += fill.taker_outcome.fee

        logger.info(f"usdc fees: {fees_default}, ddx fees: {fees_ddx}")

        if fees_default > Decimal("0"):
            insurance_fund_key = InsuranceFundKey()
            insurance_fund = self.smt.insurance_fund(insurance_fund_key)
            insurance_fund[TokenSymbol.USDC] += fees_default
            self.smt.store_insurance_fund(insurance_fund_key, insurance_fund)
        if fees_ddx > Decimal("0"):
            epoch_metadata_key = EpochMetadataKey(self.store.epoch_id)
            epoch_metadata = self.smt.epoch_metadata(epoch_metadata_key)
            epoch_metadata.ddx_fee_pool = (
                epoch_metadata.ddx_fee_pool + fees_ddx
            ).recorded_amount()
            self.smt.store_epoch_metadata(epoch_metadata_key, epoch_metadata)

    def take_orders(
        self,
        symbol: ProductSymbol,
        mark_price: Decimal,
        taker_book_order: BookOrder,
        taker_strategy_key: StrategyKey,
        taker_order_hash: str,
        matching_orders: list[tuple[BookOrderKey, BookOrder]],
        triggered_symbols_tracker: set,
    ):
        found_fill = False
        trade_outcomes = []
        solvency_rejection = False

        for matching_order_key, matching_order in matching_orders:
            maybe_fill, maybe_cancel, taker_clamped = self.take_order(
                symbol,
                mark_price,
                taker_book_order,
                (taker_strategy_key, taker_order_hash),
                matching_order_key,
                matching_order,
                triggered_symbols_tracker,
            )

            if maybe_fill is None and maybe_cancel is None:
                break

            if maybe_fill is not None:
                if not found_fill:
                    found_fill = True
                trade_outcomes.append(maybe_fill)
            if maybe_cancel is not None:
                trade_outcomes.append(maybe_cancel)

        if taker_clamped:
            solvency_rejection = True

        return trade_outcomes, found_fill, solvency_rejection

    def do_match_order(
        self,
        symbol: str,
        taker_order_hash: str,
        taker_order_type: OrderType,
        book_order: BookOrder,
        triggered_symbols_tracker: set,
        max_taker_price_deviation: Decimal,
    ):
        taker_trader_address = book_order.trader_address

        taker_strategy_key = StrategyKey(
            taker_trader_address,
            book_order.strategy_id_hash,
        )

        partial_fill_policy = (
            PartialFillPolicy.CancelRemainingAmount
            if book_order.price == Decimal("0")
            else PartialFillPolicy.PostRemainingAmount
        )

        found_self_match = False
        found_fill = False
        taker_solvency_rejection = False
        trade_outcomes = []

        mark_price = self.last_price(symbol).mark_price
        logger.debug(f"Mark price: {mark_price}")

        limit_price = book_order.price if book_order.price != Decimal("0") else None

        logger.info(
            f"Matching taker {'limit' if limit_price is not None else 'market'} order {book_order} with max take price deviation {max_taker_price_deviation}"
        )

        matching_rounds = 0
        orders_matched = False

        orders = []
        while True:
            if found_self_match or taker_solvency_rejection:
                break

            matching_rounds += 1

            logger.info(f"Matching round {matching_rounds}")
            logger.info("Filtering orders")
            (
                matching_orders,
                found_self_match,
                maybe_partial_fill_policy,
            ) = self.filter_matching_orders(
                symbol,
                book_order.side,
                mark_price,
                limit_price,
                book_order.amount,
                taker_strategy_key,
                max_taker_price_deviation,
                triggered_symbols_tracker,
            )

            if maybe_partial_fill_policy is not None:
                partial_fill_policy = maybe_partial_fill_policy

            if not matching_orders:
                logger.info("No more matching orders")
                break
            orders_matched = True
            if taker_order_type == OrderType.PostOnlyLimit:
                break

            matching_orders_len = len(matching_orders)
            orders.extend(matching_orders)

            logger.info("Taking orders")
            (trade_outcomes_, found_fill_, taker_solvency_rejection_) = self.take_orders(
                symbol,
                mark_price,
                book_order,
                taker_strategy_key,
                taker_order_hash,
                matching_orders,
                triggered_symbols_tracker,
            )

            if not found_fill and found_fill_:
                found_fill = found_fill_

            taker_solvency_rejection = taker_solvency_rejection_

            trade_outcomes_len = len(trade_outcomes_)
            trade_outcomes.extend(trade_outcomes_)

            if trade_outcomes_len < matching_orders_len:
                logger.info(f"Taker becomes insolvent!")
                partial_fill_policy = PartialFillPolicy.CancelRemainingAmount
                break

        if taker_order_type == OrderType.PostOnlyLimit and orders_matched:
            logger.info(f"Post-only order matched, rejecting order")
            return book_order, ([], False), [], partial_fill_policy, POST_ONLY_VIOLATION

        if (
            book_order.amount > Decimal("0")
            and partial_fill_policy == PartialFillPolicy.PostRemainingAmount
        ):
            self.store_book_order(BookOrderKey(symbol, taker_order_hash), book_order)

        return (
            book_order,
            (trade_outcomes, found_fill),
            orders,
            partial_fill_policy,
            None,
        )

    @log_success(OrderIntent)
    def match_order(
        self,
        matchable_intent: OrderIntent | ModifyOrderIntent,
    ) -> (
        Optional[AllPriceCheckpoints],
        Union[None, CompleteFill, PartialFill, PostOrder],
    ):
        taker_order_hash = matchable_intent.hash()
        symbol = matchable_intent.symbol
        strategy_id_hash = StrategyKey.generate_strategy_id_hash(
            matchable_intent.strategy
        )
        book_order = BookOrder(
            matchable_intent.side,
            matchable_intent.amount,
            matchable_intent.price,
            matchable_intent.recover_signer()[1],
            strategy_id_hash,
            self.products[symbol].next_book_ordinal,
            self.store.time_value,
        )

        triggered_symbols_tracker = set()
        (
            book_order,
            (trade_outcomes, found_fill),
            matching_orders,
            partial_fill_policy,
            order_rejection_reason,
        ) = self.do_match_order(
            symbol,
            taker_order_hash,
            matchable_intent.order_type,
            book_order,
            triggered_symbols_tracker,
            self.market_specs[
                self.products[symbol].tradable_product.specs
            ].max_taker_price_deviation,
        )
        if self.store.is_trade_mining() and found_fill:
            self.apply_trade_mining_rewards(
                trade_outcomes,
                matching_orders,
                book_order.trader_address,
                self.store.time_value,
            )

        price_checkpoints: dict[ProductSymbol, PriceCheckpoint] = {}
        if triggered_symbols_tracker:
            price_checkpoints = self.record_price_checkpoints(
                {
                    symbol: self.products[symbol].rolling_price
                    for symbol in triggered_symbols_tracker
                }
            )

        if order_rejection_reason == POST_ONLY_VIOLATION:
            assert not price_checkpoints and not trade_outcomes and not found_fill
            return None, None

        all_price_checkpoints = None
        if price_checkpoints:
            all_price_checkpoints = AllPriceCheckpoints(
                list(price_checkpoints.values())
            )
        trade_outcome = None
        if found_fill:
            if (
                book_order.amount == Decimal("0")
                or partial_fill_policy == PartialFillPolicy.CancelRemainingAmount
            ):
                logger.info("Complete fill")
                trade_outcome = CompleteFill(trade_outcomes)
            else:
                logger.info("Partial fill")
                trade_outcome = PartialFill(
                    Post(
                        symbol,
                        taker_order_hash,
                        book_order.side,
                        book_order.amount,
                        book_order.price,
                        book_order.trader_address,
                        strategy_id_hash,
                        book_order.book_ordinal,
                        book_order.time_value,
                    ),
                    trade_outcomes,
                )
                self.products[symbol].next_book_ordinal += 1
        elif partial_fill_policy == PartialFillPolicy.PostRemainingAmount:
            logger.info("Post order")
            trade_outcome = PostOrder(
                Post(
                    symbol,
                    taker_order_hash,
                    book_order.side,
                    book_order.amount,
                    book_order.price,
                    book_order.trader_address,
                    strategy_id_hash,
                    book_order.book_ordinal,
                    book_order.time_value,
                ),
                trade_outcomes,
            )
            self.products[symbol].next_book_ordinal += 1
        elif trade_outcomes:
            logger.info(
                "CancelRemainingAmount order with no orders taken but with trade outcomes (maker cancels), complete fill"
            )
            trade_outcome = CompleteFill(trade_outcomes)

        return all_price_checkpoints, trade_outcome

    @log_success(ModifyOrderIntent)
    def modify_order(
        self,
        modify_order_intent: ModifyOrderIntent,
    ) -> (
        Optional[Cancel],
        Optional[AllPriceCheckpoints],
        Union[None, CompleteFill, PartialFill, PostOrder],
    ):
        cancel_result = self.cancel(modify_order_intent)
        if cancel_result is None:
            return None, None, None
        return (
            cancel_result,
            *self.match_order(modify_order_intent),
        )
