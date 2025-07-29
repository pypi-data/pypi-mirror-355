"""
Sample market making implementation for the DerivaDEX exchange.

Demonstrates a basic market making strategy using the DerivaDEX client library.
Includes order management, position tracking, and deposit handling.
"""

import asyncio
import logging
import signal
from dataclasses import dataclass
from numpy.random import normal
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
    levels_to_quote : int
        Number of price levels to place orders at
    price_offset : Decimal
        Price spacing between order levels as a fraction
    quantity_per_level : Decimal
        Order size at each price level
    ref_px_deviation_to_replace_orders : Decimal
        Minimum price move required to update orders
    max_position_size : Decimal
        Maximum allowed position size in either direction
    trading_strategy : str
        Strategy identifier for order placement
    """

    symbol: str
    levels_to_quote: int
    price_offset: Decimal
    quantity_per_level: Decimal
    ref_px_deviation_to_replace_orders: Decimal
    max_position_size: Decimal
    trading_strategy: str


class MarketMaker:
    """
    Market maker implementation for the DerivaDEX exchange.

    Provides market making functionality with configurable parameters per market.
    Manages order placement, position tracking, and automatic deposits.
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
                        "levels_to_quote": {"type": "number"},
                        "price_offset": {"type": "number"},
                        "quantity_per_level": {"type": "number"},
                        "ref_px_deviation_to_replace_orders": {"type": "number"},
                        "max_position_size": {"type": "number"},
                        "trading_strategy": {"type": "string"},
                    },
                    "required": [
                        "symbol",
                        "levels_to_quote",
                        "price_offset",
                        "quantity_per_level",
                        "ref_px_deviation_to_replace_orders",
                        "max_position_size",
                        "trading_strategy",
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
        Initialize market maker with configuration.

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
        Process and validate market maker configuration.

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
                levels_to_quote=market["levels_to_quote"],
                price_offset=Decimal(str(market["price_offset"])),
                quantity_per_level=Decimal(str(market["quantity_per_level"])),
                ref_px_deviation_to_replace_orders=Decimal(
                    str(market["ref_px_deviation_to_replace_orders"])
                ),
                max_position_size=Decimal(str(market["max_position_size"])),
                trading_strategy=market["trading_strategy"],
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
                self.client.on_chain.mint_usdc(
                    self.config["collateral_address"],
                    self.client.web3_account.address,
                    deposit_amount,
                )
                self.logger.info(f"Minted {deposit_amount} USDC")
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
                    await asyncio.sleep(300)  # 5 minutes
                except asyncio.CancelledError:
                    break  # Exit immediately when cancelled
            except Exception as e:
                self.logger.error(f"Error in deposit check: {e}")

    async def _market_making_loop(self, market: MarketConfig, strategy_id: str):
        """
        Run the market making loop for a specific market-strategy pair.

        Monitors prices and maintains orders according to the configured strategy.
        Orders are updated when price moves beyond the configured threshold or
        on first run. Respects position limits and handles error recovery.

        Parameters
        ----------
        market : MarketConfig
            Configuration for the market including pricing and size parameters
        strategy_id : str
            Identifier for the trading strategy
        """

        self.logger.info(f"Starting market making loop for {market.symbol}")
        last_update_price = None

        while self.running:
            try:
                mark_price = self.client.ws.mark_price(market.symbol)
                if not mark_price:
                    self.logger.warning(f"No mark price available for {market.symbol}")
                    await asyncio.sleep(1)
                    continue

                current_price = Decimal(mark_price)

                should_update = (
                    last_update_price is None
                    or abs(current_price - last_update_price) / last_update_price
                    >= market.ref_px_deviation_to_replace_orders
                )

                if not should_update:
                    await asyncio.sleep(self.config["sleep_rate"])
                    continue

                positions_response = await self.client.account.get_positions(
                    self.config["bot_address"], strategy_id, market.symbol
                )
                position = (
                    positions_response.value[0] if positions_response.value else None
                )
                position_size = (
                    (
                        Decimal(position.balance)
                        if position.side == 1
                        else -Decimal(position.balance)
                    )
                    if position
                    else Decimal("0")
                )

                self.logger.info(
                    f"{market.symbol} - {strategy_id}: Position={position_size}, "
                    f"Price={current_price}"
                    + (
                        f" (Δ={abs(current_price - last_update_price) / last_update_price})"
                        if last_update_price is not None
                        else " (first update)"
                    )
                )

                await self._cancel_all_orders(market, strategy_id)
                await self._place_orders(
                    market, strategy_id, current_price, position_size
                )

                last_update_price = current_price

            except Exception as e:
                self.logger.error(
                    f"Error in market making loop for {market.symbol}: {e}"
                )

            await asyncio.sleep(self.config["sleep_rate"])

    async def _cancel_all_orders(self, market: MarketConfig, strategy_id: str):
        """
        Cancel all existing orders for a market-strategy pair.

        Parameters
        ----------
        market : MarketConfig
            Market configuration
        strategy_id : str
            Strategy identifier
        """

        cancel_all_intent = CancelAllIntent(
            market.symbol,
            strategy_id,
            self.client.trade.get_nonce(),
            None,
        )
        await self.client.trade.cancel_all(cancel_all_intent)

    async def _place_orders(
        self,
        market: MarketConfig,
        strategy_id: str,
        current_price: Decimal,
        position_size: Decimal,
    ):
        """
        Place limit orders at configured price levels around the current price.

        Creates a ladder of buy and sell orders, respecting position limits and
        configured parameters for order sizing and pricing. Adjusts order sizes
        based on remaining capacity in each direction.

        Parameters
        ----------
        market : MarketConfig
            Market configuration including order parameters
        strategy_id : str
            Strategy identifier for order placement
        current_price : Decimal
            Current market price to base order prices around
        position_size : Decimal
            Current position size (positive for longs, negative for shorts)
        """

        remaining_buy_size = market.max_position_size - position_size
        remaining_sell_size = market.max_position_size + position_size

        self.logger.info(
            f"Remaining capacity for {market.symbol}: "
            f"buy={remaining_buy_size}, sell={remaining_sell_size}"
        )

        for level in range(market.levels_to_quote):
            offset = market.price_offset * (level + 1)

            base_qty = float(market.quantity_per_level)
            random_qty = round_to_unit(
                Decimal(
                    max(
                        base_qty * 0.5,
                        min(
                            base_qty * 1.5,
                            normal(base_qty, base_qty * 0.25),
                        ),
                    )
                ),
                1,
            )

            if remaining_buy_size > 0:
                buy_price = round_to_unit(
                    current_price * (1 - offset), 1 if market.symbol == "ETHP" else 0
                )
                qty = min(random_qty, remaining_buy_size)
                if qty > 0:
                    self.logger.info(
                        f"Placing buy order: {qty} @ {buy_price} in {market.symbol}"
                    )
                    await self._place_order(
                        market, strategy_id, buy_price, qty, OrderSide.Bid
                    )
                    remaining_buy_size -= qty

            if remaining_sell_size > 0:
                sell_price = round_to_unit(
                    current_price * (1 + offset), 1 if market.symbol == "ETHP" else 0
                )
                qty = min(random_qty, remaining_sell_size)
                if qty > 0:
                    self.logger.info(
                        f"Placing sell order: {qty} @ {sell_price} in {market.symbol}"
                    )
                    await self._place_order(
                        market, strategy_id, sell_price, qty, OrderSide.Ask
                    )
                    remaining_sell_size -= qty

    async def _place_order(
        self,
        market: MarketConfig,
        strategy_id: str,
        price: Decimal,
        quantity: Decimal,
        side: OrderSide,
    ):
        """
        Place a single limit order with error handling.

        Parameters
        ----------
        market : MarketConfig
            Market configuration
        strategy_id : str
            Strategy identifier
        price : Decimal
            Order price
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
                OrderType.Limit,
                self.client.trade.get_nonce(),
                quantity,
                price,
                Decimal("0"),
                None,
            )
            await self.client.trade.place_order(order_intent)
        except Exception as e:
            self.logger.error(
                f"Error placing {side} order in {market.symbol}: {quantity} @ {price}: {e}"
            )

    async def start(self):
        """
        Start the market maker.

        Initializes client connection, sets up WebSocket subscriptions,
        checks deposits, and starts market making tasks for each market-strategy pair.
        Uses context manager for proper client lifecycle management.
        """

        self.logger.info("Starting market maker")
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
                            self._market_making_loop(market, strategy_id),
                            name=f"market_maker_{market.symbol}_{strategy_id}",
                        )
                        self.tasks.append(task)

                deposit_task = asyncio.create_task(
                    self._deposit_check_loop(), name="deposit_check"
                )
                self.tasks.append(deposit_task)

                self.logger.info("Market maker started")

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

                    # Then cancel orders per market/strategy
                    for market in self.markets.values():
                        for strategy_id in self.config["strategies"]:
                            try:
                                cancel_all_intent = CancelAllIntent(
                                    market.symbol,
                                    strategy_id,
                                    self.client.trade.get_nonce(),
                                    None,
                                )
                                await self.client.trade.cancel_all(cancel_all_intent)
                            except Exception as e:
                                self.logger.error(
                                    f"Error cancelling orders for {strategy_id}: {e}"
                                )

                    self.tasks = []

        except Exception as e:
            self.logger.error(f"Error in market maker: {e}")
            raise
        finally:
            self.running = False

    async def stop(self):
        """Signal the market maker to stop and clean up resources."""

        self.logger.info("Stopping market maker")
        self.running = False


async def main(config_json: dict):
    """
    Run the market maker with provided configuration.

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

    market_maker = MarketMaker(config_json)

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig, lambda: asyncio.create_task(market_maker.stop(), name="shutdown")
        )

    try:
        await market_maker.start()
    except KeyboardInterrupt:
        await market_maker.stop()
    except Exception as e:
        await market_maker.stop()
        raise


if __name__ == "__main__":
    config_json = get_config("marketmaker")
    asyncio.run(main(config_json))
