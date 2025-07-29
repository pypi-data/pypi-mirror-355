"""
Wallet module
"""

import logging

from eth_account import Account
from eth_account.signers.local import LocalAccount

logger = logging.getLogger(__name__)


class Wallet:
    def __init__(self, mnemonic: str):
        # In-memory, HD wallet like key derivation.
        Account.enable_unaudited_hdwallet_features()
        self.mnemonic = mnemonic

    def account_for_index(self, index: int) -> LocalAccount:
        acc = Account.from_mnemonic(
            self.mnemonic, account_path=f"m/44'/60'/0'/0/{index}"
        )
        logger.info(f"Eth account for index {index}: {acc.address}")
        return acc
