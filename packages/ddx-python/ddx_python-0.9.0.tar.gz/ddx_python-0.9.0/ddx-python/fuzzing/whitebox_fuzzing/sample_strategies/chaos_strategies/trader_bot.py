import asyncio
import logging
from random import getrandbits

from eth_account.signers.local import LocalAccount
from numpy.random import random, normal
from typing import List, Dict

from ddx._rust.decimal import Decimal
from ddx._rust.common.requests.intents import (
    CancelAllIntent,
    OrderIntent,
    ProfileUpdateIntent,
    WithdrawIntent,
)

from whitebox_fuzzing.test_utils.test_derivadex_client import TestDerivaDEXClient

logger = logging.getLogger(__name__)


class TraderBot:
    def __init__(
        self,
        client: TestDerivaDEXClient,
        markets: Dict[str, any],
        strategies: List,
        collateral_address: str,
        collateral_amount: Decimal,
        ddx_address: str = None,
        ddx_faucet_key: str = None,
        sleep_rate: int = 5,
    ):
        self.client = client
        self.account = self.init_account()
        self.markets = markets
        self.strategies = strategies
        self.collateral_address = collateral_address
        self.collateral_amount = collateral_amount
        self.ddx_address = ddx_address
        self.ddx_faucet_key = ddx_faucet_key
        self.sleep_rate = sleep_rate
        self.long_likelihood = random()

    @property
    def private_key(self):
        return self.account.key

    async def run(self):
        """
        Main bot execution loop.

        Sets up the bot's accounts, deposits collateral, and
        continuously executes the bot's trading behavior.
        """

        logger.info(f"Bot {self.account.address} running")

        try:
            # Add account to KYC whitelist
            await self.client.kyc.add_test_account(self.account.address)

            # Prepare collateral for the bot
            self.prepare_collateral()

            if self.ddx_faucet_key and self.ddx_address:
                await asyncio.sleep(2)
                logger.info(f"depositing DDX for bot {self.account.address}")
                try:
                    self.client.on_chain.mint_ddx(
                        self.ddx_address,
                        self.account.address,
                        Decimal("1_000_000"),
                        local_account=self.client.w3.eth.account.from_key(
                            self.ddx_faucet_key
                        ),
                    )
                    self.client.on_chain.approve_ddx(
                        self.ddx_address,
                        Decimal("1_000_000"),
                        local_account=self.account,
                    )
                    tx_receipt = await self.client.on_chain.deposit_ddx(
                        Decimal("1_000_000"), local_account=self.account
                    )
                    await self.client.on_chain.wait_for_confirmations(tx_receipt)
                    logger.info(
                        f"Bot {self.account.address} deposited DDX successfully"
                    )
                except Exception as e:
                    logging.info(f"Deposit DDX exception: {e}")

            for strategy in self.strategies:
                try:
                    await self.deposit_collateral(strategy)
                except Exception as e:
                    logger.error(f"Failed to deposit collateral for {strategy}: {e}")

            while True:
                logger.info(f"Bot {self.account.address} woke up")
                await self.behavior()

                sleep_time = normal(self.sleep_rate, 1)
                logger.info(
                    f"Bot {self.account.address} sleeping for {sleep_time:.2f} seconds"
                )
                await asyncio.sleep(max(0.1, sleep_time))

        except Exception as e:
            logger.error(f"Bot {self.account.address} encountered an error: {e}")
            raise

    async def behavior(self):
        """
        Execute the bot's trading behavior.

        Default implementation just calls trade().
        Subclasses may override for more complex behavior.
        """

        await self.trade()

    async def trade(self):
        """
        Execute trading logic.

        Must be implemented by subclasses.

        Raises
        ------
        NotImplementedError
            If not implemented by subclass
        """

        raise NotImplementedError

    def init_account(self) -> LocalAccount:
        """
        Initialize a new random Ethereum account for the bot.

        Returns
        -------
        LocalAccount
            Newly created Ethereum account
        """

        account = self.client.w3.eth.account.from_key(
            self.client.w3.keccak(getrandbits(32 * 8))
        )
        logger.info(
            f"New bot created with address: {account.address} and key {account.key.hex()}"
        )

        return account

    def prepare_collateral(self):
        """
        Mint and approve collateral tokens for the bot.
        """

        logger.info(f"Bot {self.account.address} minting and approving collateral")

        try:
            self.client.on_chain.mint_usdc(
                self.collateral_address,
                self.account.address,
                Decimal("100_000_000"),
                local_account=self.account,
            )
            self.client.on_chain.approve(
                self.collateral_address,
                Decimal("100_000_000"),
                local_account=self.account,
            )
            logger.info(f"Bot {self.account.address} prepared collateral successfully")
        except Exception as e:
            logger.error(f"Failed to prepare collateral: {e}")
            raise

    async def deposit_collateral(self, strategy: str):
        """
        Deposit collateral for a specific strategy.

        Parameters
        ----------
        strategy : str
            Strategy ID to deposit for
        """

        logger.info(
            f"Bot {self.account.address} ({self.account.key.hex()}) depositing collateral for strategy: {strategy}"
        )

        try:
            tx_receipt = await self.client.on_chain.deposit(
                self.collateral_address,
                strategy,
                self.collateral_amount,
                local_account=self.account,
            )
            await self.client.on_chain.wait_for_confirmations(tx_receipt)

            logger.info(f"Deposited {self.collateral_amount} for strategy {strategy}")

            # Random chance to update profile to pay fees in DDX
            if random() < 0.5:
                try:
                    profile_update_intent = ProfileUpdateIntent(
                        self.client.trade.get_nonce(), True
                    )
                    await self.client.trade.update_profile(
                        profile_update_intent, local_account=self.account
                    )
                    logger.info(
                        f"Updated profile for {self.account.address} to pay fees in DDX"
                    )
                except Exception as e:
                    logger.error(f"Failed to update profile: {e}")
        except Exception as e:
            logger.error(f"Failed to deposit collateral for strategy {strategy}: {e}")
            raise
