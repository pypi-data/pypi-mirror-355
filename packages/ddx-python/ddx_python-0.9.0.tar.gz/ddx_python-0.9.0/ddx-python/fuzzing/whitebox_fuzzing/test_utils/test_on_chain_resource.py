from typing import Optional
from eth_account.signers.local import LocalAccount
from web3.types import TxReceipt

from ddx._rust.decimal import Decimal

from ddx.common.utils import to_base_unit_amount
from ddx.rest_client.contracts.ddx import DDX
from ddx.rest_client.contracts.dummy_token import DummyToken
from ddx.rest_client.resources.on_chain_resource import (
    OnChainResource,
    COLLATERAL_DECIMALS,
    DDX_DECIMALS,
)


class TestOnChainResource(OnChainResource):
    """
    Test-only extensions to on-chain operations.
    Inherits production functionality and adds test-specific methods.

    Provides faucet functionality for minting test tokens and funding accounts
    with ETH. These operations are only available on test networks.
    """

    def mint_ddx(
        self,
        ddx_address: str,
        recipient_address: str,
        amount: Decimal,
        local_account: Optional[LocalAccount] = None,
    ) -> TxReceipt:
        """
        Mint DDX tokens (testnet only).

        Parameters
        ----------
        ddx_address : str
            The DDX token contract address
        recipient_address : str
            Address to receive the minted tokens
        amount : Decimal
            Amount of DDX to mint (in DDX units)
        local_account : Optional[LocalAccount]
            Local account to sign with, defaults to client's account

        Returns
        -------
        TxReceipt
            Transaction receipt

        Notes
        -----
        This operation uses the transfer function from a faucet account
        rather than direct minting. Only available on test networks.
        """

        ddx_contract = DDX(self._web3, ddx_address)
        mint_amount = to_base_unit_amount(amount, DDX_DECIMALS)

        return self._send_transaction(
            ddx_contract.transfer,
            method_params=[recipient_address, mint_amount],
            local_account=local_account,
        )

    def mint_usdc(
        self,
        collateral_address: str,
        recipient_address: str,
        amount: Decimal,
        nonce: Optional[int] = None,
        local_account: Optional[LocalAccount] = None,
    ) -> TxReceipt:
        """
        Mint USDC tokens (testnet only).

        Parameters
        ----------
        collateral_address : str
            The USDC token contract address
        recipient_address : str
            Address to receive the minted tokens
        amount : Decimal
            Amount of USDC to mint (in USDC units
        nonce : Optional[int]
            Custom nonce for the transaction
        local_account : Optional[LocalAccount]
            Local account to sign with, defaults to client's account

        Returns
        -------
        TxReceipt
            Transaction receipt

        Notes
        -----
        This operation will fail on mainnet as the token contract
        does not support minting.
        """

        dummy_token = DummyToken(self._web3, collateral_address)
        mint_amount = to_base_unit_amount(amount, COLLATERAL_DECIMALS)

        return self._send_transaction(
            dummy_token.mint,
            method_params=[recipient_address, mint_amount],
            nonce=nonce,
            local_account=local_account,
        )

    def fund_eth(
        self,
        recipient_address: str,
        amount: Decimal,
        local_account: Optional[LocalAccount] = None,
    ) -> TxReceipt:
        """
        Send ETH to an address (testnet only).

        Parameters
        ----------
        recipient_address : str
            Address to receive the ETH
        amount : Decimal
            Amount of ETH to send
        local_account : Optional[LocalAccount]
            Local account to sign with, defaults to client's account

        Returns
        -------
        TxReceipt
            Transaction receipt

        Notes
        -----
        This is a raw ETH transfer using a custom transaction rather
        than a contract method call.
        """

        account = local_account or self._web3_account

        tx = {
            "to": recipient_address,
            "value": self._web3.to_wei(str(amount), "ether"),
            "gas": 21000,
            "maxFeePerGas": 3000000000,
            "maxPriorityFeePerGas": 2000000000,
            "nonce": self._web3.eth.get_transaction_count(account.address),
            "chainId": 100,
        }

        signed_tx = self._web3.eth.account.sign_transaction(tx, private_key=account.key)
        tx_hash = self._web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = self._web3.eth.wait_for_transaction_receipt(tx_hash, poll_latency=0.5)

        return receipt
