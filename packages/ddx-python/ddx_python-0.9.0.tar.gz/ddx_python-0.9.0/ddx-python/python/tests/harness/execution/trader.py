import logging

from ddx.common.item_utils import update_avail_collateral, update_locked_collateral
from ddx.common.logging import local_logger
from ddx.common.transactions.trader_update import TraderUpdate
from ddx.common.transactions.withdraw import Withdraw
from ddx.common.transactions.withdraw_ddx import WithdrawDDX
from ddx._rust.common import TokenSymbol
from ddx._rust.common.requests.intents import (ProfileUpdateIntent,
                                                WithdrawDDXIntent,
                                                WithdrawIntent)
from ddx._rust.common.state.keys import StrategyKey, TraderKey
from ddx._rust.common.transactions import TraderUpdateKind
from ddx._rust.decimal import Decimal
from tests.harness.market_aware_account import MarketAwareAccount

from .utils import log_success

logger = local_logger(__name__)


class TraderMixin:
    @log_success(ProfileUpdateIntent)
    def update_profile(
        self,
        profile_update_intent: ProfileUpdateIntent,
    ) -> TraderUpdate:
        _, trader_address = profile_update_intent.recover_signer()
        trader_key = TraderKey(trader_address)
        trader = self.smt.trader(trader_key)
        trader.pay_fees_in_ddx = profile_update_intent.pay_fees_in_ddx
        self.smt.store_trader(trader_key, trader)
        return TraderUpdate(
            trader_address,
            Decimal("0"),
            TraderUpdateKind.Profile,
            profile_update_intent.pay_fees_in_ddx,
        )

    @log_success(WithdrawIntent)
    def intend_withdrawal(
        self,
        withdraw_intent: WithdrawIntent,
    ) -> Withdraw:
        logger.info(f"Processing withdrawal intent {withdraw_intent}")
        _, trader_address = withdraw_intent.recover_signer()

        abbrev_strategy_id_hash = StrategyKey.generate_strategy_id_hash(
            withdraw_intent.strategy_id
        )
        strategy_key = StrategyKey(
            trader_address,
            abbrev_strategy_id_hash,
        )
        strategy = self.smt.strategy(strategy_key)
        market_aware_account = MarketAwareAccount(
            strategy, self.positions_for_strategy(strategy_key)
        )
        max_withdraw_amount = market_aware_account.maximum_withdrawal_amount
        if withdraw_intent.amount > max_withdraw_amount:
            raise ValueError(
                f"Requested withdrawal amount {withdraw_intent.amount} exceeds the maximum withdrawal amount {max_withdraw_amount}"
            )
        token_symbol = TokenSymbol.from_address(withdraw_intent.currency)
        update_avail_collateral(
            strategy,
            token_symbol,
            strategy.avail_collateral[token_symbol] - withdraw_intent.amount,
        )
        update_locked_collateral(
            strategy,
            token_symbol,
            strategy.locked_collateral[token_symbol] + withdraw_intent.amount,
        )
        self.smt.store_strategy(strategy_key, strategy)
        return Withdraw(
            trader_address,
            abbrev_strategy_id_hash,
            withdraw_intent.currency,
            withdraw_intent.amount,
        )

    @log_success(WithdrawDDXIntent)
    def intend_withdrawal_ddx(
        self,
        withdraw_ddx_intent: WithdrawDDXIntent,
    ) -> WithdrawDDX:
        logger.info(f"Processing DDX withdrawal intent {withdraw_ddx_intent}")
        _, trader_address = withdraw_ddx_intent.recover_signer()
        trader_key = TraderKey(trader_address)
        trader = self.smt.trader(trader_key)
        if withdraw_ddx_intent.amount > trader.avail_ddx_balance:
            raise ValueError(
                f"Requested DDX withdrawal amount {withdraw_ddx_intent.amount} exceeds the trader's available balance {trader.avail_ddx_balance}"
            )
        trader.avail_ddx_balance -= withdraw_ddx_intent.amount
        trader.locked_ddx_balance += withdraw_ddx_intent.amount
        self.smt.store_trader(trader_key, trader)
        return WithdrawDDX(
            trader_address,
            withdraw_ddx_intent.amount,
        )
