from typing import List, Dict
import logging
from functools import cached_property

from ddx._rust.decimal import Decimal

from whitebox_fuzzing.test_utils.test_derivadex_client import TestDerivaDEXClient
from whitebox_fuzzing.sample_strategies.chaos_strategies.full_suite import FullSuiteBot
from whitebox_fuzzing.sample_strategies.chaos_strategies.large_deposit import (
    LargeDepositBot,
)


logger = logging.getLogger(__name__)


class Spawner:
    """
    Spawns chaos bot instances with different strategies.

    Handles creation of new bots with appropriate configuration
    and initial funding.
    """

    def __init__(
        self,
        client: TestDerivaDEXClient,
        collateral_address: str,
        collateral_amount: Decimal,
        chaos_strategy: str,
        markets: Dict[str, any],
        strategies: List[str],
        ddx_address: str = None,
        ddx_faucet_key: str = None,
        batch_size: int = 20,
        sleep_rate: int = 5,
    ):
        self.client = client
        self.collateral_address = collateral_address
        self.collateral_amount = collateral_amount
        self.batch_size = batch_size
        self.chaos_strategy = chaos_strategy
        self.markets = markets
        self.strategies = strategies
        self.ddx_faucet_key = ddx_faucet_key
        self.ddx_address = ddx_address
        self.sleep_rate = sleep_rate

    def spawn(self):
        """
        Create and fund a new bot instance.

        Returns
        -------
        Bot
            A new bot instance of the configured type
        """

        logger.info(f"Spawning new {self.chaos_strategy} bot")

        bot = self.bot_class(
            self.client,
            self.markets,
            self.strategies,
            self.collateral_address,
            self.collateral_amount,
            ddx_address=self.ddx_address,
            ddx_faucet_key=self.ddx_faucet_key,
            sleep_rate=self.sleep_rate,
        )

        try:
            self.client.on_chain.fund_eth(bot.account.address, Decimal("5"))
            logger.info(f"Funded bot at {bot.account.address} with 5 ETH")
        except Exception as e:
            logger.error(f"Failed to fund bot: {e}")
            # Still return the bot, it might be able to operate

        return bot

    @cached_property
    def bot_class(self):
        """
        Get the appropriate bot class based on the configured strategy.

        Returns
        -------
        type
            Bot class to instantiate

        Raises
        ------
        ValueError
            If the configured strategy is invalid
        """

        if self.chaos_strategy == "full_suite":
            return FullSuiteBot
        elif self.chaos_strategy == "large_deposit":
            return LargeDepositBot
        else:
            raise ValueError(f"Invalid chaos strategy: {self.chaos_strategy}")
