"""
Account module.
"""

import logging
from typing import Optional
from eth_abi import encode
from eth_abi.utils.padding import zpad32_right
from eth_account.signers.local import LocalAccount
from eth_utils.crypto import keccak
from zero_ex.contract_wrappers import TxParams

from ddx._rust.common import ProductSymbol, TokenSymbol
from ddx._rust.common.enums import OrderSide, OrderType
from ddx._rust.common.requests.intents import (
    CancelAllIntent,
    CancelOrderIntent,
    ModifyOrderIntent,
    OrderIntent,
    ProfileUpdateIntent,
    WithdrawDDXIntent,
    WithdrawIntent,
)
from ddx._rust.common.state.keys import StrategyKey, TraderKey
from ddx._rust.decimal import Decimal

from ddx.rest_client.contracts.checkpoint import Checkpoint
from ddx.rest_client.contracts.i_collateral import ICollateral
from ddx.rest_client.contracts.ddx import DDX as DDXContract
from ddx.rest_client.contracts.dummy_token import DummyToken
from ddx.rest_client.contracts.i_stake import IStake


logger = logging.getLogger(__name__)


class Account:
    def __init__(self, signer: LocalAccount):
        """
        An account that can perform user-driven actions versus the exchange.

        Parameters
        ----------
        signer : LocalAccount
            ETH signing material for a particular address.
        """

        from tests.harness.store import Store

        # Get initialized store instance.
        self.store = Store.the_store()

        self.signer = signer
        self.nonce = 0

    def generate_kyc_auth_signature(self, expiry_block: int):
        eip191_header = b"\x19Ethereum Signed Message:\n"

        encode_message = (
            encode(["address"], [self.store.verifying_contract_address])
            + encode(["uint256"], [self.store.chain_id])
            + encode(["address"], [self.signer.address])
            + encode(["uint256"], [expiry_block])
        )

        intermediary_hash = keccak(encode_message)
        eip191_hash = keccak(
            eip191_header
            + str(len(intermediary_hash)).encode("utf8")
            + intermediary_hash
        )
        signature = (
            self.store.wallet.account_for_index(
                0).signHash(eip191_hash).signature
        )
        return signature[64:] + signature[:64]

    async def deposit(self, strategy: str, amount: Decimal):
        """
        Approve and deposit USDC to DerivaDEX.

        Parameters
        ----------
        strategy : str
            Strategy name (only 'main' supported for now).
        amount : Decimal
            Amount to approve and subsequently deposit.
        """

        # Get USDC token contract wrapper.
        dummy_token_contract = DummyToken(
            self.store.w3, TokenSymbol.USDC.address())

        # Approve a transfer for the specified amount.
        nonce = self.store.w3.eth.get_transaction_count(self.signer.address)
        built_tx = dummy_token_contract.approve.build_transaction(
            self.store.verifying_contract_address,
            amount.to_usdc_grains(),
            tx_params=TxParams(
                from_=self.signer.address,
                nonce=nonce,
                gas_price=self.store.w3.eth.gas_price,
            ),
        )
        signed_tx = self.store.w3.eth.account.sign_transaction(
            built_tx, private_key=self.signer.key
        )

        # Send transaction and mine 1 blocks afterwards.
        await self.store.send_and_confirm_eth_tx(signed_tx.rawTransaction, 1)

        # Get the ICollateral facet contract wrapper.
        i_collateral_contract = ICollateral(
            self.store.w3, self.store.verifying_contract_address
        )

        expiry_block = self.store.w3.eth.block_number - 1 + 7_200
        kyc_auth_signature = self.generate_kyc_auth_signature(expiry_block)

        # Deposit the specified amount of USDC to the DerivaDEX contracts.
        nonce = self.store.w3.eth.get_transaction_count(self.signer.address)
        built_tx = i_collateral_contract.deposit.build_transaction(
            TokenSymbol.USDC.address(),
            zpad32_right(
                len(strategy).to_bytes(1, byteorder="little") +
                strategy.encode("utf8")
            ),
            amount.to_usdc_grains(),
            expiry_block,
            kyc_auth_signature,
            tx_params=TxParams(
                from_=self.signer.address,
                nonce=nonce,
                gas_price=self.store.w3.eth.gas_price,
            ),
        )
        signed_tx = self.store.w3.eth.account.sign_transaction(
            built_tx, private_key=self.signer.key
        )

        # Send transaction and mine 6 blocks afterwards so the operator immediately picks up the event.
        deposit_tx_hash = await self.store.send_and_confirm_eth_tx(
            signed_tx.rawTransaction,
            6,
            send_operator_requests=False,
        )

        return deposit_tx_hash

    async def deposit_ddx(self, amount: Decimal):
        """
        Approve and deposit DDX to DerivaDEX.

        Parameters
        ----------
        amount : Decimal
            Amount to approve and subsequently deposit.
        """

        # Get DDX token contract wrapper.
        ddx_token_contract = DDXContract(
            self.store.w3, TokenSymbol.DDX.address())

        # Approve a transfer for the specified amount.
        nonce = self.store.w3.eth.get_transaction_count(self.signer.address)
        built_tx = ddx_token_contract.approve.build_transaction(
            self.store.verifying_contract_address,
            amount.to_ddx_grains(),
            tx_params=TxParams(
                from_=self.signer.address,
                nonce=nonce,
                gas_price=self.store.w3.eth.gas_price,
            ),
        )
        signed_tx = self.store.w3.eth.account.sign_transaction(
            built_tx, private_key=self.signer.key
        )

        # Send transaction and mine 1 blocks afterwards.
        await self.store.send_and_confirm_eth_tx(signed_tx.rawTransaction, 1)

        # Get the IStake facet contract wrapper.
        i_stake_contract = IStake(
            self.store.w3, self.store.verifying_contract_address)

        expiry_block = self.store.w3.eth.block_number - 1 + 7_200
        kyc_auth_signature = self.generate_kyc_auth_signature(expiry_block)

        # Deposit the specified amount of DX to the DerivaDEX contracts.
        nonce = self.store.w3.eth.get_transaction_count(self.signer.address)
        built_tx = i_stake_contract.deposit_ddx.build_transaction(
            amount.to_ddx_grains(),
            expiry_block,
            kyc_auth_signature,
            tx_params=TxParams(
                from_=self.signer.address,
                nonce=nonce,
                gas_price=self.store.w3.eth.gas_price,
            ),
        )
        signed_tx = self.store.w3.eth.account.sign_transaction(
            built_tx, private_key=self.signer.key
        )

        # Send transaction and mine 6 blocks afterwards so the operator immediately picks up the event.
        deposit_tx_hash = await self.store.send_and_confirm_eth_tx(
            signed_tx.rawTransaction,
            6,
            send_operator_requests=False,
        )

        return deposit_tx_hash

    async def intend_withdrawal(self, strategy_id: str, amount: Decimal):
        """
        Intend withdrawal of USDC from DerivaDEX.

        Parameters
        ----------
        strategy_id : str
            Strategy name (only 'main' supported for now).
        amount : Decimal
            Amount to intend a withdrawal for.
        """

        withdraw_intent = WithdrawIntent(
            strategy_id,
            TokenSymbol.USDC.address(),
            amount,
            f'0x{encode(["bytes32"], [str(self.nonce).encode("utf8")]).hex()}',
        )

        # Sign the EIP-712 hash of the order intent.
        withdraw_intent.signature = self.signer.signHash(
            bytes.fromhex(withdraw_intent.hash_eip712().removeprefix("0x"))
        ).signature.hex()

        self.nonce += 1

        return withdraw_intent

    async def intend_withdrawal_ddx(self, amount: Decimal):
        """
        Intend withdrawal of DDX from DerivaDEX.

        Parameters
        ----------
        amount : Decimal
            Amount to intend a withdrawal for.
        """

        withdraw_ddx_intent = WithdrawDDXIntent(
            amount,
            f'0x{encode(["bytes32"], [str(self.nonce).encode("utf8")]).hex()}',
        )

        # Sign the EIP-712 hash of the order intent.
        withdraw_ddx_intent.signature = self.signer.signHash(
            bytes.fromhex(withdraw_ddx_intent.hash_eip712().removeprefix("0x"))
        ).signature.hex()

        self.nonce += 1

        return withdraw_ddx_intent

    async def submit_checkpoint(
        self, strategy_id: Optional[str] = None, mine_blocks: int = 6
    ):
        """
        Submit a checkpoint to DerivaDEX.

        Parameters
        ----------
        strategy_id : Optional[str]
            Strategy id to generate a merkle proof for. If None, a trader proof is generated instead.
        mine_blocks : int
            Number of blocks to mine after submitting the checkpoint.
        """

        # Generate the proof
        trader_address = f"0x00{self.signer.address[2:]}"
        proof = None
        if strategy_id is not None:
            strategy_key = StrategyKey(
                trader_address,
                StrategyKey.generate_strategy_id_hash(strategy_id),
            )
            proof = f"0x{self.store.state.proof(strategy_key.encode_key()).as_bytes().hex()}"
        else:
            trader_key = TraderKey(trader_address)
            proof = (
                f"0x{self.store.state.proof(trader_key.encode_key()).as_bytes().hex()}"
            )

        # Get the checkpoint from the state.
        checkpointed_epoch, checkpoint = self.store.state.last_created_checkpoint
        logger.info(
            f"Using checkpoint {checkpoint} from epoch {checkpointed_epoch}")
        checkpoint_contract = Checkpoint(
            self.store.w3, self.store.verifying_contract_address
        )

        # go from RSV to VRS signature
        signature = bytes.fromhex(checkpoint["signature"].removeprefix("0x"))
        signature = signature[-1:] + signature[:-1]
        signature = f"0x{signature.hex()}"

        nonce = self.store.w3.eth.get_transaction_count(self.signer.address)
        built_tx = checkpoint_contract.checkpoint.build_transaction(
            {
                "checkpointData": {
                    "blockNumber": checkpoint["blockNumber"],
                    "blockHash": checkpoint["blockHash"],
                    "stateRoot": checkpoint["stateRoot"],
                    "transactionRoot": checkpoint["transactionRoot"],
                },
                "signatures": [signature],
            },
            [],
            checkpointed_epoch,
            tx_params=TxParams(
                from_=self.signer.address,
                nonce=nonce,
            ),
        )
        signed_tx = self.store.w3.eth.account.sign_transaction(
            built_tx, private_key=self.signer.key
        )

        # Submit the checkpoint and mine 6 blocks afterwards so the operator immediately picks up the event.
        checkpoint_tx_hash = await self.store.send_and_confirm_eth_tx(
            signed_tx.rawTransaction,
            mine_blocks,
            send_operator_requests=False,
        )

        checkpointed_event = checkpoint_contract.get_checkpointed_event(
            checkpoint_tx_hash
        )[0]

        return (checkpoint_tx_hash, checkpointed_event), proof

    async def submit_invalid_checkpoint(self, mine_blocks: int = 6):
        """
        Submit an empty checkpoint to DerivaDEX.

        Parameters
        ----------
        mine_blocks : int
            Number of blocks to mine after submitting the checkpoint.
        """

        # Get the checkpoint from the state.
        checkpointed_epoch, checkpoint = self.store.state.last_created_checkpoint
        logger.info(
            f"Using checkpoint {checkpoint} from epoch {checkpointed_epoch}")
        checkpoint_contract = Checkpoint(
            self.store.w3, self.store.verifying_contract_address
        )

        nonce = self.store.w3.eth.get_transaction_count(self.signer.address)
        built_tx = checkpoint_contract.checkpoint.build_transaction(
            {
                "checkpointData": {
                    "blockNumber": checkpoint["blockNumber"],
                    "blockHash": checkpoint["blockHash"],
                    "stateRoot": checkpoint["stateRoot"],
                    "transactionRoot": checkpoint["transactionRoot"],
                },
                "signatures": ["0x" + "00" * 65],
            },
            [],
            checkpointed_epoch,
            tx_params=TxParams(
                from_=self.signer.address,
                nonce=nonce,
            ),
        )
        signed_tx = self.store.w3.eth.account.sign_transaction(
            built_tx, private_key=self.signer.key
        )

        # Submit the checkpoint and mine 6 blocks afterwards so the operator immediately picks up the event.
        checkpoint_tx_hash = await self.store.send_and_confirm_eth_tx(
            signed_tx.rawTransaction,
            mine_blocks,
            send_operator_requests=False,
        )

    async def claim_withdrawal(
        self, strategy_id_hash: str, amount: Decimal, strategy_proof: str
    ):
        """
        Claim withdrawal of USDC from DerivaDEX.

        Parameters
        ----------
        strategy_id_hash : str
            Strategy hash.
        amount : Decimal
            Amount to claim.
        strategy_proof: str
            Strategy proof.
        """

        # Get the ICollateral facet contract wrapper.
        i_collateral_contract = ICollateral(
            self.store.w3, self.store.verifying_contract_address
        )

        # Withdraw the specified amount of USDC from the DerivaDEX contracts.
        nonce = self.store.w3.eth.get_transaction_count(self.signer.address)
        collateral_address = self.store.w3.to_checksum_address(
            TokenSymbol.USDC.address()
        )

        strategy_key = StrategyKey(
            f"0x00{self.signer.address[2:]}",
            strategy_id_hash,
        )
        strategy = self.store.state.smt.strategy(strategy_key)

        checkpointed_strategy = {
            "availCollateral": {
                "tokens": [collateral_address],
                "amounts": [
                    amount.to_usdc_grains()
                    for amount in strategy.avail_collateral.amounts()
                ],
            },
            "lockedCollateral": {
                "tokens": [collateral_address],
                "amounts": [
                    amount.to_usdc_grains()
                    for amount in strategy.locked_collateral.amounts()
                ],
            },
            "maxLeverage": strategy.max_leverage,
            "frozen": strategy.frozen,
        }
        logger.info(f"Checkpointed strategy: {checkpointed_strategy}")

        withdraw_data = {
            "tokens": [collateral_address],
            "amounts": [amount.to_usdc_grains()],
        }
        logger.info(f"Withdraw data: {withdraw_data}")
        logger.info(f"Strategy proof: {strategy_proof}")

        built_tx = i_collateral_contract.withdraw.build_transaction(
            strategy_id_hash,
            withdraw_data,
            checkpointed_strategy,
            strategy_proof,
            tx_params=TxParams(
                from_=self.signer.address,
                nonce=nonce,
            ),
        )
        signed_tx = self.store.w3.eth.account.sign_transaction(
            built_tx, private_key=self.signer.key
        )
        # Send transaction and mine 6 blocks afterwards so the operator immediately picks up the event.
        withdraw_tx_hash = await self.store.send_and_confirm_eth_tx(
            signed_tx.rawTransaction,
            6,
            send_operator_requests=False,
        )

        return withdraw_tx_hash

    async def claim_withdrawal_ddx(self, amount: Decimal, trader_proof: str):
        """
        Claim withdrawal of DDX from DerivaDEX.

        Parameters
        ----------
        amount : Decimal
            Amount to claim.
        trader_proof: str
            Trader proof.
        """

        # Get the IStake facet contract wrapper.
        i_stake_contract = IStake(
            self.store.w3, self.store.verifying_contract_address)

        # Withdraw the specified amount of USDC from the DerivaDEX contracts.
        nonce = self.store.w3.eth.get_transaction_count(self.signer.address)

        trader_key = TraderKey(
            f"0x00{self.signer.address[2:]}",
        )
        trader = self.store.state.smt.trader(trader_key)

        checkpointed_trader = {
            "availDDXBalance": trader.avail_ddx_balance.to_usdc_grains(),
            "lockedDDXBalance": trader.locked_ddx_balance.to_usdc_grains(),
            "referralAddress": self.store.w3.to_checksum_address(
                trader.referral_address
            ),
            "payFeesInDDX": trader.pay_fees_in_ddx,
            "accessDenied": trader.access_denied,
        }
        logger.info(f"Checkpointed trader: {checkpointed_trader}")
        logger.info(f"Trader proof: {trader_proof}")

        built_tx = i_stake_contract.withdraw_ddx.build_transaction(
            amount.to_ddx_grains(),
            checkpointed_trader,
            trader_proof,
            tx_params=TxParams(
                from_=self.signer.address,
                nonce=nonce,
            ),
        )
        signed_tx = self.store.w3.eth.account.sign_transaction(
            built_tx, private_key=self.signer.key
        )
        # Send transaction and mine 6 blocks afterwards so the operator immediately picks up the event.
        withdraw_ddx_tx_hash = await self.store.send_and_confirm_eth_tx(
            signed_tx.rawTransaction,
            6,
            send_operator_requests=False,
        )

        return withdraw_ddx_tx_hash

    async def update_profile(
        self,
        pay_fees_in_ddx: bool,
    ):
        """
        Submit an order to DerivaDEX.

        Parameters
        ----------
        pay_fees_in_ddx : bool
            Whether to pay fees in DDX or not.
        """

        # Create a profile update intent with the specified values.
        profile_update_intent = ProfileUpdateIntent(
            f'0x{encode(["bytes32"], [str(self.nonce).encode("utf8")]).hex()}',
            pay_fees_in_ddx,
        )

        # Sign the EIP-712 hash of the profile update intent.
        # TODO: these don't take self.store.chain_id or self.store.verifying_contract_address into account
        profile_update_intent.signature = self.signer.signHash(
            bytes.fromhex(
                profile_update_intent.hash_eip712().removeprefix("0x"))
        ).signature.hex()

        self.nonce += 1

        return profile_update_intent

    async def order(
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
        Submit an order to DerivaDEX.

        Parameters
        ----------
        symbol : str
            Symbol name (e.g., 'ETHP').
        strategy : str
            Strategy name (only 'main' supported for now).
        side : OrderSide
            Order side ('Bid' | 'Ask').
        side : OrderType
            Order side ('Limit' | 'Market').
        amount : Decimal
            Order amount (e.g., Decimal('3.7')).
        price : Decimal
            Order price (e.g., Decimal('1_800.2')). A market order must be submitted with a price of Decimal('0').
        stop_price: Decimal
            Stop price (only Decimal('0') is valid for now since stops are not supported for now).
        """

        # Create an order intent with the specified values.
        order_intent = OrderIntent(
            symbol,
            strategy,
            side,
            order_type,
            f'0x{encode(["bytes32"], [str(self.nonce).encode("utf8")]).hex()}',
            amount,
            price,
            stop_price,
            None,
        )

        # Sign the EIP-712 hash of the order intent.
        order_intent.signature = self.signer.signHash(
            bytes.fromhex(order_intent.hash_eip712().removeprefix("0x"))
        ).signature.hex()

        self.nonce += 1

        return order_intent

    async def modify_order(
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
        Submit an order to DerivaDEX.

        Parameters
        ----------
        order_hash: str
            Order hash to modify.
        symbol : str
            Symbol name (e.g., 'ETHP').
        strategy : str
            Strategy name (only 'main' supported for now).
        side : OrderSide
            Order side ('Bid' | 'Ask').
        side : OrderType
            Order side ('Limit' | 'Market').
        amount : Decimal
            Order amount (e.g., Decimal('3.7')).
        price : Decimal
            Order price (e.g., Decimal('1_800.2')). A market order must be submitted with a price of Decimal('0').
        stop_price: Decimal
            Stop price (only Decimal('0') is valid for now since stops are not supported for now).
        """

        # Create an order intent with the specified values.
        modify_order_intent = ModifyOrderIntent(
            order_hash,
            symbol,
            strategy,
            side,
            order_type,
            f'0x{encode(["bytes32"], [str(self.nonce).encode("utf8")]).hex()}',
            amount,
            price,
            stop_price,
            None,
        )

        # Sign the EIP-712 hash of the order intent.
        modify_order_intent.signature = self.signer.signHash(
            bytes.fromhex(modify_order_intent.hash_eip712().removeprefix("0x"))
        ).signature.hex()

        self.nonce += 1

        return modify_order_intent

    async def cancel_all(
        self,
        symbol: ProductSymbol,
        strategy: str,
    ):
        """
        Submit an cancel all intent to DerivaDEX.

        Parameters
        ----------
        symbol : str
            Symbol name (e.g., 'ETHP').
        strategy : str
            Strategy name (only 'main' supported for now).
        """

        # Create an cancel all intent with the specified values.
        cancel_all_intent = CancelAllIntent(
            symbol,
            strategy,
            f'0x{encode(["bytes32"], [str(self.nonce).encode("utf8")]).hex()}',
            None,
        )

        # Sign the EIP-712 hash of the order intent.
        # TODO: these don't take self.store.chain_id or self.store.verifying_contract_address into account
        cancel_all_intent.signature = self.signer.signHash(
            bytes.fromhex(cancel_all_intent.hash_eip712().removeprefix("0x"))
        ).signature.hex()

        self.nonce += 1

        return cancel_all_intent

    async def cancel_order(
        self,
        symbol: ProductSymbol,
        order_hash: str,
    ):
        """
        Submit an cancel order intent to DerivaDEX.

        Parameters
        ----------
        symbol : str
            Symbol name (e.g., 'ETHP').
        order_hash : str
            Order hash to cancel.
        """

        # Create an cancel order intent with the specified values.
        cancel_order_intent = CancelOrderIntent(
            symbol,
            order_hash,
            f'0x{encode(["bytes32"], [str(self.nonce).encode("utf8")]).hex()}',
            None,
        )

        # Sign the EIP-712 hash of the order intent.
        # TODO: these don't take self.store.chain_id or self.store.verifying_contract_address into account
        cancel_order_intent.signature = self.signer.signHash(
            bytes.fromhex(cancel_order_intent.hash_eip712().removeprefix("0x"))
        ).signature.hex()

        self.nonce += 1

        return cancel_order_intent
