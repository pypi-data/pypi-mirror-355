import logging
from collections import defaultdict
from typing import Optional

from ddx.common.item_utils import update_avail_collateral, update_locked_collateral
from ddx.common.logging import local_logger
from ddx.common.transactions.advance_epoch import AdvanceEpoch as AdvanceEpochTx
from ddx.common.transactions.fee_distribution import FeeDistribution
from ddx.common.transactions.signer_registered import SignerRegistered
from ddx.common.transactions.strategy_update import StrategyUpdate
from ddx.common.transactions.trader_update import TraderUpdate
from ddx.common.utils import calculate_max_collateral
from ddx._rust.common import TokenSymbol
from ddx._rust.common.requests import AdvanceEpoch, Block
from ddx._rust.common.state import EpochMetadata, Signer, Strategy, Trader
from ddx._rust.common.state.keys import (EpochMetadataKey, SignerKey,
                                          StrategyKey, TraderKey)
from ddx._rust.common.transactions import StrategyUpdateKind, TraderUpdateKind
from ddx._rust.decimal import Decimal
from tests.harness.account import Account
from web3.datastructures import AttributeDict

from .utils import log_success

logger = local_logger(__name__)


def split_fees(pooled: Decimal, weights: list[Decimal]) -> Optional[list[Decimal]]:
    total_weights = sum(weights)
    if pooled != Decimal("0") and total_weights > Decimal("0"):
        shares_per_unit = pooled / total_weights
        return [w * shares_per_unit for w in weights]
    return None


class BlockMixin:
    @log_success(AdvanceEpoch)
    def advance_epoch(self, request: AdvanceEpoch) -> AdvanceEpochTx:
        logger.info(f"Advancing epoch {request}")

        # Update next book ordinals of the current epoch
        old_epoch_metadata_key = EpochMetadataKey(self.store.epoch_id)
        old_epoch_metadata = self.smt.epoch_metadata(old_epoch_metadata_key)
        next_book_ordinals = {
            symbol: product.next_book_ordinal
            for symbol, product in self.products.items()
        }
        old_epoch_metadata.next_book_ordinals = next_book_ordinals
        self.smt.store_epoch_metadata(old_epoch_metadata_key, old_epoch_metadata)

        # Create a new epoch
        self.smt.store_epoch_metadata(
            EpochMetadataKey(request.epoch_id),
            EpochMetadata.default(),
        )

        return AdvanceEpochTx(
            next_book_ordinals,
            request.epoch_id,
        )

    @log_success(Block)
    def deposit(
        self,
        account: Account,
        collateral_address: str,
        strategy_id: str,
        amount: Decimal,
        deposit_tx_hash: str,
    ) -> StrategyUpdate:
        logger.info(
            f"Depositing {amount} from {collateral_address} into strategy {strategy_id} for account {account.signer.address}"
        )
        strategy_id_hash = StrategyKey.generate_strategy_id_hash(strategy_id)
        trader_address = f"0x00{account.signer.address[2:]}"
        trader_key: TraderKey = TraderKey(trader_address)
        trader = self.smt.trader(trader_key)
        if trader is None:
            trader = Trader.default()
            self.smt.store_trader(trader_key, trader)

        strategy_key: StrategyKey = StrategyKey(trader_address, strategy_id_hash)
        strategy = self.smt.strategy(strategy_key)
        if strategy is None:
            strategy = Strategy()
        max_allowable_deposit = max(
            Decimal("0"),
            calculate_max_collateral(self.collateral_tranches, trader.avail_ddx_balance)
            - strategy.avail_collateral.total_value(),
        )
        net_amount = min(amount, max_allowable_deposit)
        token_symbol = TokenSymbol.from_address(collateral_address)
        update_avail_collateral(
            strategy,
            token_symbol,
            strategy.avail_collateral[token_symbol] + net_amount,
        )
        if amount > net_amount:
            kickback_amount = amount - net_amount
            update_locked_collateral(
                strategy,
                token_symbol,
                strategy.locked_collateral[token_symbol] + kickback_amount,
            )
        self.smt.store_strategy(strategy_key, strategy)
        return StrategyUpdate(
            trader_address,
            collateral_address,
            strategy_id_hash,
            strategy_id,
            amount,
            StrategyUpdateKind.Deposit,
            deposit_tx_hash,
        )

    @log_success(Block)
    def deposit_ddx(
        self,
        account: Account,
        amount: Decimal,
        deposit_ddx_tx_hash: str,
    ) -> TraderUpdate:
        logger.info(f"Depositing {amount} from for account {account.signer.address}")
        trader_address = f"0x00{account.signer.address[2:]}"
        trader_key: TraderKey = TraderKey(trader_address)
        trader = self.smt.trader(trader_key)
        if trader is None:
            trader = Trader.default()
        trader.avail_ddx_balance += amount
        self.smt.store_trader(trader_key, trader)
        return TraderUpdate(
            trader_address,
            amount,
            TraderUpdateKind.DepositDDX,
            trader.pay_fees_in_ddx,
            deposit_ddx_tx_hash,
        )

    @log_success(Block)
    def checkpoint(self, checkpointed_event: AttributeDict) -> FeeDistribution:
        checkpointed_event = checkpointed_event.args
        logger.info(f"Read checkpointed event {checkpointed_event}")

        custodians = [f"0x00{address[2:]}" for address in checkpointed_event.custodians]
        # we need the bond to be in (fractional) units of DDX
        bonds = [Decimal.from_ddx_grains(bond) for bond in checkpointed_event.bonds]
        submitter_address = f"0x00{checkpointed_event.submitter[2:]}"
        logger.info(
            f"After sanitization: custodians {custodians}, bonds {bonds}, submitter {submitter_address}"
        )
        # Epoch metadatas only exist as far back as the first trading epoch
        epochs = range(
            max(self.last_checkpointed_epoch, 1), self.last_created_checkpoint[0] + 1
        )
        logger.info(f"Collecting fee pool information for epochs {epochs}")
        combined_fee_pool = Decimal("0")
        for epoch_id in epochs:
            epoch_metadata_key = EpochMetadataKey(epoch_id)
            epoch_metadata = self.smt.epoch_metadata(epoch_metadata_key)
            combined_fee_pool += epoch_metadata.ddx_fee_pool
            self.smt.store_epoch_metadata(epoch_metadata_key, None)

        payments = defaultdict(Decimal)
        if combined_fee_pool != Decimal("0"):
            total_distributed_fees = Decimal("0")
            # TODO: equal weights for now
            if (
                parts := split_fees(
                    combined_fee_pool,
                    [Decimal("1") for _ in checkpointed_event.custodians],
                )
            ) is not None:
                for address, amount in zip(custodians, parts):
                    trader_key: TraderKey = TraderKey(address)
                    trader = self.smt.trader(trader_key)
                    balance = trader.avail_ddx_balance
                    trader.avail_ddx_balance = (balance + amount).recorded_amount()
                    if trader.avail_ddx_balance != balance:
                        self.smt.store_trader(trader_key, trader)
                        rounded_diff = trader.avail_ddx_balance - balance
                        total_distributed_fees += rounded_diff
                        payments[address] = rounded_diff
            dust = combined_fee_pool - total_distributed_fees
            submitter = self.smt.trader(TraderKey(submitter_address))
            balance = submitter.avail_ddx_balance
            submitter.avail_ddx_balance += dust
            if submitter.avail_ddx_balance != balance:
                self.smt.store_trader(submitter_key, submitter)
                payments[f"0x00{account.signer.address[2:]}"] += dust
        self.last_checkpointed_epoch = self.last_created_checkpoint[0]
        return FeeDistribution(
            custodians,
            bonds,
            submitter_address,
            self.last_created_checkpoint[0],
        )

    @log_success(Block)
    def claim_withdrawal(
        self,
        account: Account,
        collateral_address: str,
        strategy_id_hash: str,
        amount: Decimal,
        withdraw_tx_hash: str,
    ) -> StrategyUpdate:
        trader_address = f"0x00{account.signer.address[2:]}"
        strategy_key = StrategyKey(
            f"0x00{account.signer.address[2:]}",
            strategy_id_hash,
        )
        strategy = self.smt.strategy(strategy_key)
        token_symbol = TokenSymbol.from_address(collateral_address)
        update_locked_collateral(
            strategy, token_symbol, strategy.locked_collateral[token_symbol] - amount
        )
        self.smt.store_strategy(strategy_key, strategy)
        return StrategyUpdate(
            trader_address,
            collateral_address,
            strategy_id_hash,
            None,
            amount,
            StrategyUpdateKind.Withdraw,
            withdraw_tx_hash,
        )

    @log_success(Block)
    def claim_withdrawal_ddx(
        self,
        account: Account,
        amount: Decimal,
        withdraw_ddx_tx_hash: str,
    ) -> TraderUpdate:
        trader_address = f"0x00{account.signer.address[2:]}"
        trader_key: TraderKey = TraderKey(trader_address)
        trader = self.smt.trader(trader_key)
        trader.locked_ddx_balance -= amount
        self.smt.store_trader(trader_key, trader)
        return TraderUpdate(
            trader_address,
            amount,
            TraderUpdateKind.WithdrawDDX,
            trader.pay_fees_in_ddx,
            withdraw_ddx_tx_hash,
        )

    @log_success(Block)
    def register_signer(
        self, release_hash: str, signer_address: str
    ) -> Optional[SignerRegistered]:
        logger.info(
            f"Registering signer {signer_address} with release hash {release_hash}"
        )
        signer_key = SignerKey(signer_address)
        signer = self.smt.signer(signer_key)
        if signer is not None:
            logger.info(f"Skipping unexpected signer already registered {signer}")
            return None
        self.smt.store_signer(signer_key, Signer(release_hash))
        return SignerRegistered(signer_address, release_hash)
