"""
Account module with test matchers
"""

import copy
import logging
from typing import Optional

import tests.python_only
from attrs import define, field
from ddx.common.transactions.all_price_checkpoints import AllPriceCheckpoints
from ddx.common.transactions.cancel import Cancel
from ddx.common.transactions.cancel_all import CancelAll
from ddx.common.transactions.complete_fill import CompleteFill
from ddx.common.transactions.inner.trade_fill import TradeFill
from ddx.common.transactions.partial_fill import PartialFill
from ddx.common.transactions.post_order import PostOrder
from ddx.common.transactions.trader_update import TraderUpdate
from ddx._rust.common import ProductSymbol, TokenSymbol
from ddx._rust.common.enums import OrderSide, OrderType
from ddx._rust.common.requests import Block
from ddx._rust.common.state.keys import PositionKey, StrategyKey
from ddx._rust.decimal import Decimal
from tests.harness.account import Account
from tests.harness.matchers.utils import assert_tx_eq
from web3.exceptions import ContractLogicError

logger = logging.getLogger(__name__)


@define
class AccountMatcher:
    """
    Defines an AccountMatcher.

    An AccountMatcher is responsible for matching an Account's actions with the expected transactions.

    Attributes:
        account (Account): Account instance.
        position_ids (dict[int, PositionKey]): Mapping of incrementing order nonces to PositionKeys.
    """

    account: Account
    position_ids: dict[int, PositionKey] = field(factory=dict, init=False)

    async def should_deposit(self, strategy: str, amount: Decimal):
        """
        Deposit to the exchange.

        Parameters
        ----------
        strategy : str
            Strategy name (only 'main' supported for now).
        amount : Decimal
            Deposit amount (e.g., Decimal('5_000')).
        """

        deposit_tx_hash = await self.account.deposit(strategy, amount)

        before_local_smt = copy.deepcopy(self.account.store.state.smt)

        expected = self.account.store.state.deposit(
            self.account,
            TokenSymbol.USDC.address(),
            strategy,
            amount,
            deposit_tx_hash,
        )

        next_block_number = self.account.store.w3.eth.block_number - 7 + 1
        for i in range(7):
            block = Block(next_block_number + i)
            actual = await self.account.store.send_and_audit_request(
                block,
                ((before_local_smt, self.account.store.state.root) if i == 6 else None),
            )
            if i == 6:
                return assert_tx_eq(expected, actual)

    async def should_not_deposit_min_amount_not_met(
        self, strategy: str, amount: Decimal
    ):
        """
        Deposit should fail due to the minimum deposit amount not being met.

        Parameters
        ----------
        strategy : str
            Strategy name (only 'main' supported for now).
        amount : Decimal
            Deposit amount (e.g., Decimal('5_000')).
        """

        try:
            await self.account.deposit(
                strategy,
                amount,
            )
        except ContractLogicError:
            pass
        else:
            raise AssertionError(
                "Deposit should fail due to the minimum deposit amount not being met"
            )

    async def should_deposit_ddx(self, amount: Decimal):
        """
        Deposit DDX to the exchange.

        Parameters
        ----------
        amount : Decimal
            Deposit amount (e.g., Decimal('5_000')).
        """

        deposit_tx_hash = await self.account.deposit_ddx(
            amount,
        )

        before_local_smt = copy.deepcopy(self.account.store.state.smt)

        expected = self.account.store.state.deposit_ddx(
            self.account,
            amount,
            deposit_tx_hash,
        )

        next_block_number = self.account.store.w3.eth.block_number - 7 + 1
        for i in range(7):
            block = Block(next_block_number + i)
            actual = await self.account.store.send_and_audit_request(
                block,
                ((before_local_smt, self.account.store.state.root) if i == 6 else None),
            )
            if i == 6:
                return assert_tx_eq(expected, actual)

    async def should_intend_withdraw(self, strategy_id: str, amount: Decimal):
        """
        Withdraw from the exchange.

        Parameters
        ----------
        strategy_id: str
            Strategy name (only 'main' supported for now).
        amount : Decimal
            Withdrawal amount (e.g., Decimal('5_000')).
        """

        nonce = self.account.nonce
        withdraw_intent = await self.account.intend_withdrawal(strategy_id, amount)

        before_local_smt = copy.deepcopy(self.account.store.state.smt)
        expected = self.account.store.state.intend_withdrawal(
            withdraw_intent,
        )
        actual = await self.account.store.send_and_audit_request(
            withdraw_intent,
            (before_local_smt, self.account.store.state.root),
        )

        return assert_tx_eq(expected, actual), nonce

    # TODO 3644: this requires the sequencer to be tested in the harness; right now, directly executing, it succeeds with no transactions but with a withdraw rejection.
    # async def should_reject_withdrawal_intent_insufficient_balance(
    #     self, strategy_id: str, amount: Decimal
    # ):
    #     """
    #     Withdrawal intent should be rejected due to an insufficient balance.
    #
    #     Parameters
    #     ----------
    #     strategy_id: str
    #         Strategy name (only 'main' supported for now).
    #     amount : Decimal
    #         Withdrawal amount (e.g., Decimal('5_000')).
    #     """
    #     nonce = self.account.nonce
    #     withdraw_intent = await self.account.intend_withdrawal(strategy_id, amount)
    #     logger.info(
    #         f"{await self.account.store.send_and_audit_request(withdraw_intent, None)}"
    #     )

    async def should_intend_withdraw_ddx(self, amount: Decimal):
        """
        Withdraw DDX from the exchange.

        Parameters
        ----------
        amount : Decimal
            Withdrawal amount (e.g., Decimal('5_000')).
        """

        nonce = self.account.nonce
        withdraw_ddx_intent = await self.account.intend_withdrawal_ddx(amount)

        before_local_smt = copy.deepcopy(self.account.store.state.smt)
        expected = self.account.store.state.intend_withdrawal_ddx(
            withdraw_ddx_intent,
        )
        actual = await self.account.store.send_and_audit_request(
            withdraw_ddx_intent,
            (before_local_smt, self.account.store.state.root),
        )

        return assert_tx_eq(expected, actual), nonce

    async def should_submit_valid_checkpoint(self, strategy_id: Optional[str] = None):
        """
        Should submit a valid price checkpoint to the contract.

        Parameters
        ----------
        strategy_id: Optional[str]
            Strategy name (only 'main' supported for now).
        """

        (_, checkpointed_event), proof = await self.account.submit_checkpoint(
            strategy_id
        )

        before_local_smt = copy.deepcopy(self.account.store.state.smt)

        expected = self.account.store.state.checkpoint(checkpointed_event)

        next_block_number = self.account.store.w3.eth.block_number - 7 + 1
        for i in range(7):
            block = Block(next_block_number + i)
            actual = await self.account.store.send_and_audit_request(
                block,
                (before_local_smt, self.account.store.state.root) if i == 6 else None,
            )
            if i == 6:
                return assert_tx_eq(expected, actual), proof

    async def should_submit_invalid_checkpoint(self):
        """
        Should submit an invalid price checkpoint to the contract.

        Parameters
        ----------
        """

        try:
            await self.account.submit_invalid_checkpoint()
        except ContractLogicError:
            pass
        else:
            raise AssertionError(
                "Checkpoint should fail due to its invalidity")

    async def should_claim_withdrawal(
        self, strategy_id: str, amount: Decimal, strategy_proof: str
    ):
        """
        Should successfully claim a withdrawal from the contract.

        Parameters
        ----------
        strategy_id: str
            Strategy name (only 'main' supported for now).
        amount : Decimal
            Withdrawal amount (e.g., Decimal('5_000')).
        strategy_proof: str
            Strategy proof for the withdrawal.
        """

        strategy_id_hash = StrategyKey.generate_strategy_id_hash(strategy_id)

        withdraw_tx_hash = await self.account.claim_withdrawal(
            strategy_id_hash, amount, strategy_proof
        )

        before_local_smt = copy.deepcopy(self.account.store.state.smt)

        expected = self.account.store.state.claim_withdrawal(
            self.account,
            TokenSymbol.USDC.address(),
            strategy_id_hash,
            amount,
            withdraw_tx_hash,
        )

        next_block_number = self.account.store.w3.eth.block_number - 7 + 1
        for i in range(7):
            block = Block(next_block_number + i)
            actual = await self.account.store.send_and_audit_request(
                block,
                (before_local_smt, self.account.store.state.root) if i == 6 else None,
            )
            if i == 6:
                return assert_tx_eq(expected, actual)

    async def should_reject_withdrawal_claim(
        self, strategy_id: str, amount: Decimal, strategy_proof: str
    ):
        """
        Should reject a withdrawal claim from the contract.

        Parameters
        ----------
        strategy_id: str
            Strategy name (only 'main' supported for now).
        amount : Decimal
            Withdrawal amount (e.g., Decimal('5_000')).
        strategy_proof: str
            Strategy proof for the withdrawal.
        """

        try:
            await self.account.claim_withdrawal(
                StrategyKey.generate_strategy_id_hash(strategy_id),
                amount,
                strategy_proof,
            )
        except ContractLogicError:
            pass
        else:
            raise AssertionError(
                "Withdrawal claim should fail due to an invalid strategy proof"
            )

    async def should_claim_withdrawal_ddx(self, amount: Decimal, trader_proof: str):
        """
        Should successfully claim a DDX withdrawal from the contract.

        Parameters
        ----------
        amount : Decimal
            Withdrawal amount (e.g., Decimal('5_000')).
        trader_proof: str
            Trader proof for the withdrawal.
        """

        withdraw_ddx_tx_hash = await self.account.claim_withdrawal_ddx(
            amount, trader_proof
        )

        before_local_smt = copy.deepcopy(self.account.store.state.smt)

        expected = self.account.store.state.claim_withdrawal_ddx(
            self.account,
            amount,
            withdraw_ddx_tx_hash,
        )

        next_block_number = self.account.store.w3.eth.block_number - 7 + 1
        for i in range(7):
            block = Block(next_block_number + i)
            actual = await self.account.store.send_and_audit_request(
                block,
                (before_local_smt, self.account.store.state.root) if i == 6 else None,
            )
            if i == 6:
                return assert_tx_eq(expected, actual)

    async def should_reject_withdrawal_ddx_claim(
        self, amount: Decimal, trader_proof: str
    ):
        """
        Should reject a DDX withdrawal claim from the contract.

        Parameters
        ----------
        amount : Decimal
            Withdrawal amount (e.g., Decimal('5_000')).
        trader_proof: str
            Trader proof for the withdrawal.
        """

        try:
            await self.account.claim_withdrawal_ddx(amount, trader_proof)
        except ContractLogicError:
            pass
        else:
            raise AssertionError(
                "DDX withdrawal claim should fail due to an invalid trader proof"
            )

    async def should_update_profile(
        self,
        pay_fees_in_ddx: bool,
    ):
        """
        Should submit a profile update to DerivaDEX.

        Parameters
        ----------
        pay_fees_in_ddx : bool
            Whether to pay fees in DDX or not.
        """

        nonce = self.account.nonce
        profile_update_intent = await self.account.update_profile(
            pay_fees_in_ddx,
        )

        before_local_smt = copy.deepcopy(self.account.store.state.smt)

        expected = self.account.store.state.update_profile(
            profile_update_intent,
        )

        actual = await self.account.store.send_and_audit_request(
            profile_update_intent,
            (before_local_smt, self.account.store.state.root),
        )
        profile_update_tx = next(
            filter(
                lambda tx: isinstance(tx, TraderUpdate),
                assert_tx_eq(expected, actual),
            )
        )

        return profile_update_tx, nonce

    async def should_order(
        self,
        symbol: ProductSymbol,
        strategy: str,
        side: OrderSide,
        order_type: OrderType,
        amount: Decimal,
        price: Decimal,
        stop_price: Decimal,
    ):
        """
        Should submit an order to DerivaDEX.

        Parameters
        ----------
        symbol : str
            Symbol name (e.g., 'ETHPERP').
        strategy : str
            Strategy name (only 'main' supported for now).
        side : OrderSide
            Order side ('Bid' | 'Ask').
        order_type : OrderType
            Order type ('Limit' | 'Market').
        amount : Decimal
            Order amount (e.g., Decimal('3.7')).
        price : Decimal
            Order price (e.g., Decimal('1_800.2')). A market order must be submitted with a price of Decimal('0').
        stop_price: Decimal
            Stop price (only Decimal('0') is valid for now since stops are not supported for now).
        """
        nonce = self.account.nonce
        order_intent = await self.account.order(
            symbol,
            strategy,
            side,
            order_type,
            amount,
            price,
            stop_price,
        )

        before_local_smt = copy.deepcopy(self.account.store.state.smt)

        expected = self.account.store.state.match_order(
            order_intent,
        )
        actual = await self.account.store.send_and_audit_request(
            order_intent,
            (before_local_smt, self.account.store.state.root),
        )

        return assert_tx_eq(expected, actual), nonce

    async def should_post_order(
        self,
        symbol: ProductSymbol,
        strategy: str,
        side: OrderSide,
        order_type: OrderType,
        amount: Decimal,
        price: Decimal,
        stop_price: Decimal,
    ):
        """
        Should submit an order to DerivaDEX that gets posted to the book.

        Parameters
        ----------
        symbol : str
            Symbol name (e.g., 'ETHPERP').
        strategy : str
            Strategy name (only 'main' supported for now).
        side : OrderSide
            Order side ('Bid' | 'Ask').
        order_type : OrderType
            Order type ('Limit' | 'Market').
        amount : Decimal
            Order amount (e.g., Decimal('3.7')).
        price : Decimal
            Order price (e.g., Decimal('1_800.2')). A market order must be submitted with a price of Decimal('0').
        stop_price: Decimal
            Stop price (only Decimal('0') is valid for now since stops are not supported for now).
        """

        actual, nonce = await self.should_order(
            symbol, strategy, side, order_type, amount, price, stop_price
        )

        post_order_tx = next(
            filter(
                lambda tx: isinstance(tx, PostOrder),
                actual,
            )
        )

        self.position_ids[nonce] = PositionKey(
            post_order_tx.post.trader_address,
            post_order_tx.post.strategy_id_hash,
            post_order_tx.post.symbol,
        )

        return post_order_tx, (nonce, post_order_tx.post.order_hash)

    async def should_complete_or_partial_fill_order(
        self,
        symbol: ProductSymbol,
        strategy: str,
        side: OrderSide,
        order_type: OrderType,
        amount: Decimal,
        price: Decimal,
        stop_price: Decimal,
    ):
        """
        Should submit an order to DerivaDEX that either complete or partial fills an existing order on the book.

        Parameters
        ----------
        symbol : str
            Symbol name (e.g., 'ETHPERP').
        strategy : str
            Strategy name (only 'main' supported for now).
        side : OrderSide
            Order side ('Bid' | 'Ask').
        order_type : OrderType
            Order side ('Limit' | 'Market').
        amount : Decimal
            Order amount (e.g., Decimal('3.7')).
        price : Decimal
            Order price (e.g., Decimal('1_800.2')). A market order must be submitted with a price of Decimal('0').
        stop_price: Decimal
            Stop price (only Decimal('0') is valid for now since stops are not supported for now).
        """

        actual, nonce = await self.should_order(
            symbol, strategy, side, order_type, amount, price, stop_price
        )

        fill_tx = next(
            filter(
                lambda tx: isinstance(
                    tx, CompleteFill) or isinstance(tx, PartialFill),
                actual,
            )
        )

        if isinstance(fill_tx, CompleteFill):
            fill = next(
                filter(
                    lambda trade_outcome: isinstance(trade_outcome, TradeFill),
                    fill_tx.trade_outcomes,
                )
            )
            self.position_ids[nonce] = PositionKey(
                fill.taker_outcome.trader,
                fill.taker_outcome.strategy_id_hash,
                fill.symbol,
            )
        else:
            self.position_ids[nonce] = PositionKey(
                fill_tx.post.trader_address,
                fill_tx.post.strategy_id_hash,
                fill_tx.post.symbol,
            )

        return fill_tx, nonce

    async def should_complete_fill_order(
        self,
        symbol: ProductSymbol,
        strategy: str,
        side: OrderSide,
        order_type: OrderType,
        amount: Decimal,
        price: Decimal,
        stop_price: Decimal,
    ):
        """
        Should submit an order to DerivaDEX that matches with an existing order on the book.

        Parameters
        ----------
        symbol : str
            Symbol name (e.g., 'ETHPERP').
        strategy : str
            Strategy name (only 'main' supported for now).
        side : OrderSide
            Order side ('Bid' | 'Ask').
        order_type : OrderType
            Order side ('Limit' | 'Market').
        amount : Decimal
            Order amount (e.g., Decimal('3.7')).
        price : Decimal
            Order price (e.g., Decimal('1_800.2')). A market order must be submitted with a price of Decimal('0').
        stop_price: Decimal
            Stop price (only Decimal('0') is valid for now since stops are not supported for now).
        """

        complete_fill_tx, nonce = await self.should_complete_or_partial_fill_order(
            symbol, strategy, side, order_type, amount, price, stop_price
        )

        assert isinstance(complete_fill_tx, CompleteFill)

        return complete_fill_tx, nonce

    async def should_partial_fill_order(
        self,
        symbol: ProductSymbol,
        strategy: str,
        side: OrderSide,
        order_type: OrderType,
        amount: Decimal,
        price: Decimal,
        stop_price: Decimal,
    ):
        """
        Should submit an order to DerivaDEX that partial fills one or more existing orders on the book.

        Parameters
        ----------
        symbol : str
            Symbol name (e.g., 'ETHPERP').
        strategy : str
            Strategy name (only 'main' supported for now).
        side : OrderSide
            Order side ('Bid' | 'Ask').
        order_type : OrderType
            Order side ('Limit' | 'Market').
        amount : Decimal
            Order amount (e.g., Decimal('3.7')).
        price : Decimal
            Order price (e.g., Decimal('1_800.2')). A market order must be submitted with a price of Decimal('0').
        stop_price: Decimal
            Stop price (only Decimal('0') is valid for now since stops are not supported for now).
        """

        partial_fill_tx, nonce = await self.should_complete_or_partial_fill_order(
            symbol, strategy, side, order_type, amount, price, stop_price
        )

        assert isinstance(partial_fill_tx, PartialFill)

        return partial_fill_tx, nonce

    async def should_complete_fill_order_cancel_remainder(
        self,
        symbol: ProductSymbol,
        strategy: str,
        side: OrderSide,
        order_type: OrderType,
        amount: Decimal,
        price: Decimal,
        stop_price: Decimal,
    ):
        """
        Should submit an order to DerivaDEX that complete fills to an amount less than the order intended.

        Parameters
        ----------
        symbol : str
            Symbol name (e.g., 'ETHPERP').
        strategy : str
            Strategy name (only 'main' supported for now).
        side : OrderSide
            Order side ('Bid' | 'Ask').
        order_type : OrderType
            Order side ('Limit' | 'Market').
        amount : Decimal
            Order amount (e.g., Decimal('3.7')).
        price : Decimal
            Order price (e.g., Decimal('1_800.2')). A market order must be submitted with a price of Decimal('0').
        stop_price: Decimal
            Stop price (only Decimal('0') is valid for now since stops are not supported for now).
        """

        complete_fill_tx, nonce = await self.should_complete_fill_order(
            symbol,
            strategy,
            side,
            order_type,
            amount,
            price,
            stop_price,
        )

        # Check that the filled amount is less than the order amount, even though the order is complete.
        actual_amount = sum(
            trade_outcome.amount
            for trade_outcome in complete_fill_tx.trade_outcomes
            if isinstance(trade_outcome, TradeFill)
        )
        logger.info(
            f"cancel remainder? filled amount = {actual_amount} < {amount} = intended amount"
        )
        assert actual_amount < amount

        return complete_fill_tx, nonce

    async def should_partial_fill_order_partial_post(
        self,
        symbol: ProductSymbol,
        strategy: str,
        side: OrderSide,
        order_type: OrderType,
        amount: Decimal,
        price: Decimal,
        stop_price: Decimal,
    ):
        """
        Should submit an order to DerivaDEX that partial fills and posts an amount less than (order intent amount - partial fill amount).

        Parameters
        ----------
        symbol : str
            Symbol name (e.g., 'ETHPERP').
        strategy : str
            Strategy name (only 'main' supported for now).
        side : OrderSide
            Order side ('Bid' | 'Ask').
        order_type : OrderType
            Order side ('Limit' | 'Market').
        amount : Decimal
            Order amount (e.g., Decimal('3.7')).
        price : Decimal
            Order price (e.g., Decimal('1_800.2')). A market order must be submitted with a price of Decimal('0').
        stop_price: Decimal
            Stop price (only Decimal('0') is valid for now since stops are not supported for now).
        """

        partial_fill_tx, nonce = await self.should_partial_fill_order(
            symbol,
            strategy,
            side,
            order_type,
            amount,
            price,
            stop_price,
        )

        # Check that the posted amount is less than the difference between the order intent amount and the partial fill amount.
        calculated_amount = amount - sum(
            trade_outcome.amount
            for trade_outcome in partial_fill_tx.trade_outcomes
            if isinstance(trade_outcome, TradeFill)
        )
        logger.info(
            f"partial post? posted amount = {partial_fill_tx.post.amount} < calculated post amount (intent amount - partial fill amount) {calculated_amount}"
        )
        assert partial_fill_tx.post.amount < calculated_amount

        return partial_fill_tx, nonce

    async def should_take_no_orders(
        self,
        symbol: ProductSymbol,
        strategy: str,
        side: OrderSide,
        order_type: OrderType,
        amount: Decimal,
        price: Decimal,
        stop_price: Decimal,
        with_trade_outcomes: bool,
    ):
        """
        Should submit an order to DerivaDEX that takes no orders. Might have a state-transitioning price checkpoint, however.

        Parameters
        ----------
        symbol : str
            Symbol name (e.g., 'ETHPERP').
        strategy : str
            Strategy name (only 'main' supported for now).
        side : OrderSide
            Order side ('Bid' | 'Ask').
        order_type : OrderType
            Order side ('Limit' | 'Market').
        amount : Decimal
            Order amount (e.g., Decimal('3.7')).
        price : Decimal
            Order price (e.g., Decimal('1_800.2')). A market order must be submitted with a price of Decimal('0').
        stop_price: Decimal
            Stop price (only Decimal('0') is valid for now since stops are not supported for now).
        """

        actual, nonce = await self.should_order(
            symbol, strategy, side, order_type, amount, price, stop_price
        )

        if with_trade_outcomes:
            assert actual is not None
            complete_fill_tx = next(
                filter(
                    lambda tx: isinstance(tx, CompleteFill),
                    actual,
                )
            )

            assert all(
                isinstance(outcome, Cancel)
                for outcome in complete_fill_tx.trade_outcomes
            )
        else:
            assert (
                actual is None
                or len(actual) == 1
                and isinstance(actual[0], AllPriceCheckpoints)
            )

    async def should_modify_order(
        self,
        order_hash: str,
        symbol: ProductSymbol,
        strategy: str,
        side: OrderSide,
        order_type: OrderType,
        amount: Decimal,
        price: Decimal,
        stop_price: Decimal,
    ):
        """
        Should submit an intent to modify an order to DerivaDEX.

        Parameters
        ----------
        order_hash: str
            Order hash to modify.
        symbol : str
            Symbol name (e.g., 'ETHPERP').
        strategy : str
            Strategy name (only 'main' supported for now).
        side : OrderSide
            Order side ('Bid' | 'Ask').
        order_type : OrderType
            Order type ('Limit' | 'Market').
        amount : Decimal
            Order amount (e.g., Decimal('3.7')).
        price : Decimal
            Order price (e.g., Decimal('1_800.2')). A market order must be submitted with a price of Decimal('0').
        stop_price: Decimal
            Stop price (only Decimal('0') is valid for now since stops are not supported for now).
        """
        nonce = self.account.nonce
        modify_intent = await self.account.modify_order(
            order_hash,
            symbol,
            strategy,
            side,
            order_type,
            amount,
            price,
            stop_price,
        )

        before_local_smt = copy.deepcopy(self.account.store.state.smt)

        expected = self.account.store.state.modify_order(
            modify_intent,
        )

        actual = await self.account.store.send_and_audit_request(
            modify_intent,
            (before_local_smt, self.account.store.state.root),
        )

        return assert_tx_eq(expected, actual), nonce

    async def should_not_modify_order(
        self,
        order_hash: str,
        symbol: ProductSymbol,
        strategy: str,
        side: OrderSide,
        order_type: OrderType,
        amount: Decimal,
        price: Decimal,
        stop_price: Decimal,
    ):
        """
        Should submit an intent to modify an order to DerivaDEX that does not result in an actual cancel or repost.

        Parameters
        ----------
        order_hash: str
            Order hash to modify.
        symbol : str
            Symbol name (e.g., 'ETHPERP').
        strategy : str
            Strategy name (only 'main' supported for now).
        side : OrderSide
            Order side ('Bid' | 'Ask').
        order_type : OrderType
            Order type ('Limit' | 'Market').
        amount : Decimal
            Order amount (e.g., Decimal('3.7')).
        price : Decimal
            Order price (e.g., Decimal('1_800.2')). A market order must be submitted with a price of Decimal('0').
        stop_price: Decimal
            Stop price (only Decimal('0') is valid for now since stops are not supported for now).
        """
        actual, _ = await self.should_modify_order(
            order_hash, symbol, strategy, side, order_type, amount, price, stop_price
        )

        assert actual is None

    async def should_cancel_order(
        self,
        symbol: ProductSymbol,
        order_hash: str,
    ):
        """
        Should submit a cancel order intent to DerivaDEX that results in cancelling an order matching an order hash.

        Parameters
        ----------
        symbol : str
            Symbol name (e.g., 'ETHPERP').
        order_hash : str
            Order hash to cancel.
        """

        cancel_intent = await self.account.cancel_order(symbol, order_hash)

        before_local_smt = copy.deepcopy(self.account.store.state.smt)

        expected = self.account.store.state.cancel(cancel_intent)

        actual = await self.account.store.send_and_audit_request(
            cancel_intent,
            (before_local_smt, self.account.store.state.root),
        )

        # TODO: may need to store the position id for the cancelled order

        return assert_tx_eq(expected, actual)

    async def should_not_cancel_order(
        self,
        symbol: ProductSymbol,
        order_hash: str,
    ):
        """
        Should submit a cancel order intent to DerivaDEX that does not result in an actual cancellation.

        Parameters
        ----------
        symbol : str
            Symbol name (e.g., 'ETHPERP').
        order_hash : str
            Order hash to cancel.
        """
        actual = await self.should_cancel_order(symbol, order_hash)

        assert actual is None

    async def should_cancel_all(
        self,
        symbol: ProductSymbol,
        strategy: str,
    ):
        """
        Should submit a cancel all intent to DerivaDEX that results in cancelling all orders for a symbol.

        Parameters
        ----------
        symbol : str
            Symbol name (e.g., 'ETHPERP').
        strategy : str
            Strategy name (only 'main' supported for now).
        """

        nonce = self.account.nonce
        cancel_all_intent = await self.account.cancel_all(
            symbol,
            strategy,
        )

        before_local_smt = copy.deepcopy(self.account.store.state.smt)

        expected = self.account.store.state.cancel_all(
            cancel_all_intent,
        )

        actual = await self.account.store.send_and_audit_request(
            cancel_all_intent,
            (before_local_smt, self.account.store.state.root),
        )
        cancel_all_tx = next(
            filter(
                lambda tx: isinstance(tx, CancelAll),
                assert_tx_eq(expected, actual),
            )
        )

        self.position_ids[nonce] = PositionKey(
            cancel_all_tx.trader_address,
            cancel_all_tx.strategy_id_hash,
            cancel_all_tx.symbol,
        )

        return cancel_all_tx, nonce
