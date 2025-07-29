"""
Sample market taking implementation for the DerivaDEX exchange.

Demonstrates a basic market taking strategy using the DerivaDEX client library.
Includes order management, position tracking, and deposit handling.
"""

import asyncio
import logging
import signal
from dataclasses import dataclass
from numpy.random import uniform, random
from typing import Dict, Optional, List
import jsonschema

from ddx._rust.common.enums import OrderSide, OrderType
from ddx._rust.common.requests.intents import CancelAllIntent, OrderIntent
from ddx._rust.decimal import Decimal

from ddx.rest_client.exceptions.exceptions import (
    InvalidRequestError,
    FailedRequestError,
)
from ddx.rest_client.models.account import StrategyResponse, TraderProfileResponse
from whitebox_fuzzing.test_utils.test_derivadex_client import TestDerivaDEXClient
from ddx.realtime_client.models import (
    Feed,
    FeedWithParams,
    MarkPriceParams,
)
from utils.utils import round_to_unit, exchange_is_up, get_config

fmt_str = "[%(asctime)s] %(levelname)s @ line %(lineno)d: %(message)s"
logging.basicConfig(level=logging.INFO, format=fmt_str)
logger = logging.getLogger(__name__)


@dataclass
class MarketConfig:
    """
    Configuration parameters for market making on a single market.

    Parameters
    ----------
    symbol : str
        Trading pair symbol (e.g., 'ETHP')
    quantity : Decimal
        Base order size
    """

    symbol: str
    quantity: Decimal


class MarketTaker:
    """
    Market taker implementation for the DerivaDEX exchange.

    Provides market taking functionality with configurable parameters per market.
    Manages order placement and automatic deposits.
    Uses WebSocket feeds for real-time market data and position updates.
    """

    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "webserver_url": {"type": "string"},
            "contract_deployment": {"type": "string"},
            "rpc_url": {"type": "string"},
            "deposit_minimum": {"type": "number"},
            "deposit_amount": {"type": "number"},
            "sleep_rate": {"type": "number"},
            "bot_address": {"type": "string"},
            "private_key": {"type": "string"},
            "faucet_private_key": {"type": "string"},
            "markets": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "quantity": {"type": "number"},
                    },
                    "required": [
                        "symbol",
                        "quantity",
                    ],
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
            "deposit_minimum",
            "deposit_amount",
            "sleep_rate",
            "bot_address",
            "private_key",
            "markets",
            "strategies",
        ],
    }

    def __init__(self, config: dict):
        """
        Initialize market taker with configuration.

        Parameters
        ----------
        config : dict
            Configuration dictionary containing connection details,
            market parameters, and strategy settings

        Raises
        ------
        jsonschema.exceptions.ValidationError
            If configuration doesn't match required schema
        """

        self.logger = logging.getLogger(__name__)
        self.client: Optional[TestDerivaDEXClient] = None
        self.running = False
        self.markets: Dict[str, MarketConfig] = {}
        self.tasks: List[asyncio.Task] = []

        jsonschema.validate(config, self.CONFIG_SCHEMA)
        self.config = self._process_config(config)

    def _process_config(self, config: dict) -> dict:
        """
        Process and validate market taker configuration.

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

    async def _get_account_info(
        self, strategy_id: str
    ) -> tuple[Optional[StrategyResponse], Optional[TraderProfileResponse]]:
        """
        Get strategy and trader information.

        Returns
        -------
        tuple[Optional[StrategyResponse], Optional[TraderProfileResponse]]
            Strategy response and trader profile response objects, or None if not found
        """

        strategy_response = None
        trader_profile_response = None

        try:
            strategy_response = await self.client.account.get_strategy(
                self.client.web3_account.address, strategy_id
            )
            self.logger.info(
                f"Strategy {strategy_id} has {strategy_response.value.avail_collateral} collateral available"
            )
        except (InvalidRequestError, FailedRequestError) as e:
            self.logger.error(f"Account API error: {e.message}")
        except Exception as e:
            self.logger.error(f"Unexpected error getting strategy: {str(e)}")

        try:
            trader_profile_response = await self.client.account.get_trader_profile(
                self.client.web3_account.address
            )
            self.logger.info(
                f"Trader has {trader_profile_response.value.avail_ddx} DDX available"
            )
        except (InvalidRequestError, FailedRequestError) as e:
            self.logger.error(f"Account API error: {e.message}")
        except Exception as e:
            self.logger.error(f"Unexpected error getting strategy: {str(e)}")

        return strategy_response, trader_profile_response

    async def _check_and_deposit(self) -> None:
        """
        Check collateral levels and deposit more if below minimum threshold.

        Monitors collateral levels for each strategy and automatically initiates
        deposits when levels fall below configured minimum. Includes approval
        transaction before deposit when needed.

        Raises
        ------
        RuntimeError
            If client is not initialized
        DerivaDEXError
            If deposit or approval transactions fail
        """

        if not self.client:
            raise RuntimeError("Client not initialized")

        for strategy_id in self.config["strategies"]:
            strategy_response, trader_profile_response = await self._get_account_info(
                strategy_id
            )

            if (
                strategy_response is None
                or strategy_response.value is None
                or Decimal(strategy_response.value.avail_collateral)
                < Decimal(str(self.config["deposit_minimum"]))
            ):
                if self.config["faucet_private_key"] is not None and (
                    trader_profile_response is None
                    or trader_profile_response.value is None
                    or Decimal(trader_profile_response.value.avail_ddx)
                    < Decimal("1_000_000")
                ):
                    self.client.on_chain.mint_ddx(
                        self.config["ddx_address"],
                        self.client.web3_account.address,
                        Decimal("1_000_000"),
                        local_account=self.client.w3.eth.account.from_key(
                            self.config["faucet_private_key"]
                        ),
                    )
                    self.client.on_chain.approve_ddx(
                        self.config["ddx_address"],
                        Decimal("1_000_000"),
                    )
                    tx_receipt = await self.client.on_chain.deposit_ddx(
                        Decimal("1_000_000"),
                    )
                    await self.client.on_chain.wait_for_confirmations(tx_receipt)

                deposit_amount = Decimal(str(self.config["deposit_amount"]))
                self.logger.info(
                    f"Collateral below minimum ({self.config['deposit_minimum']}). "
                    f"Depositing {deposit_amount}"
                )

                self.client.on_chain.approve(
                    self.config["collateral_address"], deposit_amount
                )
                self.logger.info(f"Approved {deposit_amount} for deposit")

                tx_receipt = await self.client.on_chain.deposit(
                    self.config["collateral_address"], strategy_id, deposit_amount
                )
                await self.client.on_chain.wait_for_confirmations(tx_receipt)
                self.logger.info(
                    f"Deposited {deposit_amount} to strategy {strategy_id}"
                )

    async def _deposit_check_loop(self):
        """
        Run periodic loop to check and maintain deposit levels.

        Runs continuously while market maker is active, checking deposit levels
        every 5 minutes and initiating deposits when needed.
        """

        while self.running:
            try:
                await self._check_and_deposit()
                try:
                    await asyncio.sleep(300)
                except asyncio.CancelledError:
                    break
            except Exception as e:
                self.logger.error(f"Error in deposit check: {e}")

    async def _market_taking_loop(self, market: MarketConfig, strategy_id: str):
        """
        Run the market taking loop for a specific market-strategy pair.

        Places market orders with random sizes and directions.

        Parameters
        ----------
        market : MarketConfig
            Configuration for the market including size parameters
        strategy_id : str
            Identifier for the trading strategy
        """

        self.logger.info(f"Starting market taking loop for {market.symbol}")

        while self.running:
            try:
                mark_price = self.client.ws.mark_prices.get_price(market.symbol)
                if not mark_price:
                    self.logger.warning(f"No mark price available for {market.symbol}")
                    await asyncio.sleep(1)
                    continue

                # Random order size between 0.1 and 2 * configured quantity
                quantity = round_to_unit(
                    Decimal(str(uniform(0.1, float(market.quantity * 2)))),
                    1,
                )

                side = OrderSide.Bid if random() < 0.5 else OrderSide.Ask

                await self._place_order(market, strategy_id, quantity, side)

            except Exception as e:
                self.logger.error(
                    f"Error in market taking loop for {market.symbol}: {e}"
                )

            await asyncio.sleep(self.config["sleep_rate"])

    async def _place_order(
        self,
        market: MarketConfig,
        strategy_id: str,
        quantity: Decimal,
        side: OrderSide,
    ):
        """
        Place a single market order with error handling.

        Parameters
        ----------
        market : MarketConfig
            Market configuration
        strategy_id : str
            Strategy identifier
        quantity : Decimal
            Order quantity
        side : OrderSide
            Order side (Bid/Ask)
        """

        try:
            order_intent = OrderIntent(
                market.symbol,
                strategy_id,
                side,
                OrderType.Market,
                self.client.trade.get_nonce(),
                quantity,
                Decimal("0"),
                Decimal("0"),
                None,
            )
            await self.client.trade.place_order(order_intent)
        except Exception as e:
            self.logger.error(
                f"Error placing {side} order in {market.symbol}: {quantity}: {e}"
            )

    async def start(self):
        """
        Start the market taker.

        Initializes client connection, sets up WebSocket subscriptions,
        checks deposits, and starts market taking tasks for each market-strategy pair.
        Uses context manager for proper client lifecycle management.
        """

        self.logger.info("Starting market taker")
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
                self.config[
                    "collateral_address"
                ] = deployment_info.addresses.usdc_address
                self.config["ddx_address"] = deployment_info.addresses.ddx_address

                await client.ws.subscribe_feeds(
                    [
                        FeedWithParams(
                            feed=Feed.MARK_PRICE,
                            params=MarkPriceParams(symbols=["ETHP", "BTCP"]),
                        )
                    ]
                )

                await self._check_and_deposit()

                for market in self.markets.values():
                    for strategy_id in self.config["strategies"]:
                        task = asyncio.create_task(
                            self._market_taking_loop(market, strategy_id),
                            name=f"market_taker_{market.symbol}_{strategy_id}",
                        )
                        self.tasks.append(task)

                deposit_task = asyncio.create_task(
                    self._deposit_check_loop(), name="deposit_check"
                )
                self.tasks.append(deposit_task)

                self.logger.info("Market taker started")

                try:
                    while self.running:
                        await asyncio.sleep(1)
                except asyncio.CancelledError:
                    self.logger.info("Received cancellation")
                finally:
                    self.logger.info("Starting cleanup")

                    # First cancel all tasks
                    for task in self.tasks:
                        if not task.done():
                            task.cancel()

                    # Wait for tasks with timeout
                    if self.tasks:
                        try:
                            await asyncio.wait(self.tasks, timeout=5)
                        except asyncio.TimeoutError:
                            self.logger.error("Timeout waiting for tasks to cancel")

                    self.tasks = []

        except Exception as e:
            self.logger.error(f"Error in market taker: {e}")
            raise
        finally:
            self.running = False

    async def stop(self):
        """Signal the market taker to stop and clean up resources."""

        self.logger.info("Stopping market taker")
        self.running = False


async def main(config_json: dict):
    """
    Run the market taker with provided configuration.

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

    market_taker = MarketTaker(config_json)

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig, lambda: asyncio.create_task(market_taker.stop(), name="shutdown")
        )

    try:
        await market_taker.start()
    except KeyboardInterrupt:
        await market_taker.stop()
    except Exception as e:
        await market_taker.stop()
        raise


if __name__ == "__main__":
    config_json = get_config("markettaker")
    asyncio.run(main(config_json))
