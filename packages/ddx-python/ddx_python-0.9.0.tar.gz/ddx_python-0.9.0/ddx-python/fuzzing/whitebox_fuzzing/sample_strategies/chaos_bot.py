"""
DerivaDEX chaos bot
"""

import asyncio
import logging
import os
import signal
from dataclasses import dataclass
from typing import Dict, Optional, Set
import jsonschema

from ddx._rust.decimal import Decimal

from whitebox_fuzzing.test_utils.test_derivadex_client import TestDerivaDEXClient
from ddx.realtime_client.models import (
    Feed,
    FeedWithParams,
    MarkPriceParams,
)
from utils.utils import get_config, exchange_is_up
from whitebox_fuzzing.sample_strategies.chaos_strategies.spawner import Spawner


fmt_str = "[%(asctime)s] %(levelname)s @ line %(lineno)d: %(message)s"
log_level = os.environ.get("PYTHON_LOG").upper() if "PYTHON_LOG" in os.environ else 100
logging.basicConfig(level=log_level, format=fmt_str)
logger = logging.getLogger(__name__)


@dataclass
class MarketConfig:
    """
    Configuration parameters for chaos trading on a single market.

    Parameters
    ----------
    symbol : str
        Trading pair symbol (e.g., 'ETHP')
    quantity : Decimal
        Base order size
    """

    symbol: str
    quantity: Decimal


class ChaosBot:
    """
    Chaos bot implementation for the DerivaDEX exchange.

    Spawns multiple trading bots with random behaviors to create
    diverse market conditions and stress test the exchange infrastructure.
    """

    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "webserver_url": {"type": "string"},
            "contract_deployment": {"type": "string"},
            "rpc_url": {"type": "string"},
            "deposit_amount": {"type": "number"},
            "sleep_rate": {"type": "number"},
            "num_accounts": {"type": "number"},
            "bot_address": {"type": "string"},
            "private_key": {"type": "string"},
            "faucet_private_key": {"type": "string"},
            "chaos_strategy": {"type": "string"},
            "markets": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "quantity": {"type": "number"},
                    },
                    "required": ["symbol", "quantity"],
                },
                "minItems": 1,
                "uniqueItems": True,
            },
            "strategies": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": [
            "webserver_url",
            "contract_deployment",
            "rpc_url",
            "deposit_amount",
            "sleep_rate",
            "num_accounts",
            "bot_address",
            "private_key",
            "chaos_strategy",
            "markets",
            "strategies",
        ],
    }

    def __init__(self, config: dict):
        """
        Initialize chaos bot with configuration.

        Parameters
        ----------
        config : dict
            Configuration dictionary containing connection details,
            market parameters, and chaos settings

        Raises
        ------
        jsonschema.exceptions.ValidationError
            If configuration doesn't match required schema
        """

        self.logger = logging.getLogger(__name__)
        self.client: Optional[TestDerivaDEXClient] = None
        self.running = False
        self.markets: Dict[str, MarketConfig] = {}
        self.bot_tasks: Set[asyncio.Task] = set()
        self.spawner: Optional[Spawner] = None

        jsonschema.validate(config, self.CONFIG_SCHEMA)
        self.config = self._process_config(config)

    def _process_config(self, config: dict) -> dict:
        """
        Process and validate chaos bot configuration.

        Converts market configurations into MarketConfig objects and validates
        all required parameters are present.

        Parameters
        ----------
        config : dict
            Raw configuration dictionary

        Returns
        -------
        dict
            Processed configuration with validated values
        """

        self.markets = {
            market["symbol"]: MarketConfig(
                symbol=market["symbol"],
                quantity=Decimal(str(market["quantity"])),
            )
            for market in config["markets"]
        }

        self.logger.info(f"Loaded configuration for {len(self.markets)} markets")

        return config

    async def _spawn_bots(self):
        """
        Spawn the configured number of chaos trading bots.

        Creates and starts multiple trading bots with randomized behaviors
        based on the configured chaos strategy.
        """

        for i in range(self.config["num_accounts"]):
            self.logger.info(f"Spawning bot {i+1}/{self.config['num_accounts']}")
            try:
                bot = self.spawner.spawn()
                task = asyncio.create_task(bot.run(), name=f"chaos_bot_{i}")
                self.bot_tasks.add(task)
                task.add_done_callback(self.bot_tasks.discard)

                # Small delay between spawns to avoid overwhelming the system
                await asyncio.sleep(0.5)
            except Exception as e:
                self.logger.error(f"Error spawning bot {i+1}: {e}")

    async def _monitor_bots(self):
        """
        Monitor running bots and log status periodically.
        """

        while self.running and self.bot_tasks:
            self.logger.info(f"{len(self.bot_tasks)} bots are running")
            await asyncio.sleep(5)

    async def start(self):
        """
        Start the chaos bot system.

        Initializes client connection, sets up WebSocket subscriptions,
        initializes the bot spawner, and starts the configured number of bots.
        Uses context manager for proper client lifecycle management.
        """

        self.logger.info("Starting chaos bot system")
        self.running = True

        ddx_client = TestDerivaDEXClient(
            base_url=self.config["webserver_url"],
            rpc_url=self.config["rpc_url"],
            contract_deployment=self.config["contract_deployment"],
            private_key=self.config["private_key"],
        )

        try:
            async with ddx_client as client:
                self.client = client

                # Get deployment info for addresses
                deployment_info = await client.system.get_deployment_info(
                    self.config["contract_deployment"]
                )
                collateral_address = deployment_info.addresses.usdc_address
                ddx_address = deployment_info.addresses.ddx_address

                await client.ws.subscribe_feeds(
                    [
                        FeedWithParams(
                            feed=Feed.MARK_PRICE,
                            params=MarkPriceParams(symbols=["ETHP", "BTCP"]),
                        )
                    ]
                )

                # Initialize spawner with client and config
                self.spawner = Spawner(
                    client,
                    collateral_address,
                    Decimal(str(self.config["deposit_amount"])),
                    self.config["chaos_strategy"],
                    self.markets,
                    self.config["strategies"],
                    ddx_address=ddx_address,
                    ddx_faucet_key=self.config.get("faucet_private_key"),
                    sleep_rate=self.config["sleep_rate"],
                )

                # Spawn and monitor bots
                await self._spawn_bots()
                await self._monitor_bots()

        except Exception as e:
            self.logger.error(f"Error in chaos bot system: {e}")
            raise
        finally:
            self.running = False
            await self.stop()

    async def stop(self):
        """
        Stop the chaos bot system and clean up resources.

        Cancels all running bot tasks and ensures proper shutdown.
        """

        self.logger.info("Stopping chaos bot system")
        self.running = False

        # Cancel all bot tasks
        for task in list(self.bot_tasks):
            if not task.done():
                task.cancel()

        # Wait for tasks with timeout
        if self.bot_tasks:
            try:
                await asyncio.wait(list(self.bot_tasks), timeout=5)
            except asyncio.TimeoutError:
                self.logger.error("Timeout waiting for bot tasks to cancel")

        self.bot_tasks.clear()
        self.logger.info("Chaos bot system stopped")


async def main(config_json: dict):
    """
    Run the chaos bot system with provided configuration.

    Parameters
    ----------
    config_json : dict
        Parsed configuration dictionary
    """

    if not exchange_is_up(
        config_json["webserver_url"], config_json["contract_deployment"]
    ):
        # If exchange is not up yet...

        raise RuntimeError(f"exchange at {config_json['webserver_url']} is not up")

    chaos_bot = ChaosBot(config_json)

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig, lambda: asyncio.create_task(chaos_bot.stop(), name="shutdown")
        )

    try:
        await chaos_bot.start()
    except KeyboardInterrupt:
        await chaos_bot.stop()
    except Exception as e:
        await chaos_bot.stop()
        raise


if __name__ == "__main__":
    config_json = get_config("chaos")
    asyncio.run(main(config_json))
