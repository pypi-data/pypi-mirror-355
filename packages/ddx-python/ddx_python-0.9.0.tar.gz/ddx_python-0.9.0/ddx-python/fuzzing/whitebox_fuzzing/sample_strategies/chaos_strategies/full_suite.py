import logging
from typing import Optional
from numpy.random import random, uniform, choice

from ddx._rust.decimal import Decimal
from ddx._rust.common.enums import OrderSide, OrderType
from ddx._rust.common.requests.intents import (
    CancelAllIntent,
    OrderIntent,
    WithdrawIntent,
)

from ddx.rest_client.exceptions.exceptions import (
    InvalidRequestError,
    FailedRequestError,
)
from ddx.rest_client.models.account import StrategyResponse, TraderProfileResponse
from whitebox_fuzzing.sample_strategies.chaos_strategies.trader_bot import TraderBot
from utils.utils import round_to_unit


logger = logging.getLogger(__name__)


class FullSuiteBot(TraderBot):
    """
    Bot that exercises the full suite of trading operations.

    Performs a mix of trading, withdrawals, and deposit operations to
    stress test the exchange's functionality across multiple dimensions.
    """

    # Probability of performing a withdrawal instead of trading.
    p_withdraw = 0.05

    # Probability of preparing additional collateral when deposit fails.
    p_prepare_collateral = 0.5

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
                self.account.address, strategy_id
            )
            logger.info(
                f"Strategy {strategy_id} has {strategy_response.value.avail_collateral} collateral available"
            )
        except (InvalidRequestError, FailedRequestError) as e:
            logger.error(f"Account API error: {e.message}")
        except Exception as e:
            logger.error(f"Unexpected error getting strategy: {str(e)}")

        try:
            trader_profile_response = await self.client.account.get_trader_profile(
                self.account.address
            )
            logger.info(
                f"Trader has {trader_profile_response.value.avail_ddx} DDX available"
            )
        except (InvalidRequestError, FailedRequestError) as e:
            logger.error(f"Account API error: {e.message}")
        except Exception as e:
            logger.error(f"Unexpected error getting strategy: {str(e)}")

        return strategy_response, trader_profile_response

    async def behavior(self):
        """
        Decide between trading or withdrawing based on probability.

        This creates a mix of different operations to test system resilience.
        """

        # Randomly choose between withdrawal and trading.
        if random() <= FullSuiteBot.p_withdraw:
            await self.withdraw()
        else:
            await self.trade()

    async def trade(self):
        """
        Execute trading logic with randomized parameters.

        Places orders with varying sizes, types, and prices.
        """

        # Select random market and strategy to trade.
        market = choice(list(self.markets.values()))
        strategy = choice(self.strategies)

        # Get latest price from WebSocket state.
        latest_price = self.client.ws.mark_price(market.symbol)

        if not latest_price:
            logger.info(f"No price available for {market.symbol}")
            return

        base_px = Decimal(latest_price)
        logger.info(f"Trading {market.symbol} at price {base_px}")

        try:
            # Determine order side based on long_likelihood parameter.
            side = OrderSide.Bid if random() < self.long_likelihood else OrderSide.Ask

            # Random order size between 0.1 and 2 * configured quantity.
            quantity = round_to_unit(
                Decimal(str(uniform(0.1, float(market.quantity * 2)))),
                1,
            )

            # Select random order type.
            order_type = choice([OrderType.Limit, OrderType.Market])

            # Calculate price based on order type and side.
            # For limit orders, pick a random price below current price for buys,
            # or above current price for sells.
            price = (
                round_to_unit(
                    (
                        Decimal(str(uniform(0, float(base_px))))
                        if side == OrderSide.Bid
                        else Decimal(str(uniform(float(base_px), 2 * float(base_px))))
                    ),
                    1 if market.symbol == "ETHP" else 0,
                )
                if order_type == OrderType.Limit
                else Decimal("0")
            )

            # Create order intent with generated parameters.
            order_intent = OrderIntent(
                market.symbol,
                strategy,
                side,
                order_type,
                self.client.trade.get_nonce(),
                quantity,
                price,
                Decimal("0"),
                None,
            )

            # Submit the order to the exchange using the bot's account.
            place_order_response = await self.client.trade.place_order(
                order_intent, local_account=self.account
            )

            if place_order_response.t == "Sequenced":
                # Order was successfully placed.
                logger.info(f"Placed order for {quantity} {market.symbol} at {price}")
            elif place_order_response.t in ["Error", "SafetyFailure"]:
                # Handle API error responses.
                error_message = place_order_response.c.message
                logger.error(f"Order placement failed: {error_message}")

                # Handle specific error types based on the message.
                await self._handle_error_response(
                    error_message, strategy, market.symbol
                )
        except Exception as e:
            # Silently handle exceptions to continue bot operation.
            logger.error(f"Exception during trading: {str(e)}")

    async def _handle_error_response(
        self, error_message: str, strategy: str, symbol: str
    ):
        """
        Handle specific error responses from the API.

        Parameters
        ----------
        error_message : str
            The error message from the API
        strategy : str
            The strategy ID that was used
        symbol : str
            The market symbol that was used
        """

        # Check for collateral-related errors that indicate insufficient funds.
        if (
            "Minimum collateral requirements breached" in error_message
            or "Trader making request has no strategies" in error_message
            or f"Specified strategy id {strategy} not found for trader" in error_message
        ):
            # Try to deposit more collateral to resolve the issue.
            try:
                logger.info(f"Depositing more collateral for strategy {strategy}")
                await self.deposit_collateral(strategy)
            except Exception as deposit_error:
                logger.error(f"Error depositing collateral: {deposit_error}")

                # With some probability, try preparing even more collateral.
                if random() <= self.p_prepare_collateral:
                    logger.info(
                        f"Preparing additional collateral for {self.account.address}"
                    )
                    self.prepare_collateral()

        # Handle case where there are too many open orders.
        elif "Too many open orders for the current market" in error_message:
            # Cancel all existing orders for this market/strategy.
            try:
                logger.info(
                    f"Cancelling all orders for {symbol} in strategy {strategy}"
                )
                cancel_intent = CancelAllIntent(
                    symbol,
                    strategy,
                    self.client.trade.get_nonce(),
                    None,
                )
                await self.client.trade.cancel_all(
                    cancel_intent, local_account=self.account
                )
            except Exception as cancel_error:
                logger.error(f"Error cancelling orders: {cancel_error}")

    async def withdraw(self):
        """
        Execute withdrawal logic to test deposit/withdrawal flows.

        Attempts both on-chain and off-chain withdrawals with random amounts.
        """

        # Randomly choose strategy.
        strategy_id = choice(self.strategies)

        # Get strategy information.
        strategy_response, _ = await self._get_account_info(strategy_id)

        # Attempt off-chain withdrawal if strategy exists and has collateral.
        if (
            strategy_response is not None
            and strategy_response.value is not None
            and strategy_response.value.avail_collateral > Decimal("0")
        ):
            # Choose random withdrawal amount up between [0, 2 * avail_collateral].
            amount = round_to_unit(
                Decimal(
                    str(
                        uniform(
                            0,
                            float(
                                Decimal("2") * strategy_response.value.avail_collateral
                            ),
                        )
                    )
                ),
                6,
            )

            # Create and submit withdrawal intent.
            withdraw_intent = WithdrawIntent(
                strategy_id,
                self.collateral_address,
                amount,
                self.client.trade.get_nonce(),
            )
            await self.client.trade.withdraw(
                withdraw_intent, local_account=self.account
            )
            logger.info(f"Submitted off-chain withdrawal for {amount} collateral")

        # Attempt on-chain withdrawal.
        try:
            # Get strategy information.
            strategy_response, _ = await self._get_account_info(strategy_id)

            # Calculate random withdrawal amount.
            withdraw_amount = round_to_unit(
                Decimal(
                    str(
                        uniform(0, 2 * float(strategy_response.value.locked_collateral))
                    )
                ),
                6,
            )

            # Execute on-chain withdrawal.
            tx_receipt = await self.client.on_chain.withdraw(
                self.collateral_address,
                strategy_id,
                withdraw_amount,
                local_account=self.account,
            )
            await self.client.on_chain.wait_for_confirmations(tx_receipt)
            logger.info(
                f"Completed on-chain withdraw for address {self.account.address}"
            )
        except Exception as e:
            logger.error(f"Error withdrawing on-chain: {e}")
