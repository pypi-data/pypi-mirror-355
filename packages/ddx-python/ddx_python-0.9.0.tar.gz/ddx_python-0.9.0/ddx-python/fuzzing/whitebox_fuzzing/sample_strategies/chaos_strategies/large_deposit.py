import logging
from numpy.random import choice, random, uniform

from ddx._rust.common.enums import OrderSide, OrderType
from ddx._rust.common.requests.intents import CancelAllIntent, OrderIntent
from ddx._rust.decimal import Decimal

from utils.utils import round_to_unit
from whitebox_fuzzing.sample_strategies.chaos_strategies.trader_bot import TraderBot

logger = logging.getLogger(__name__)


class LargeDepositBot(TraderBot):
    """
    Bot that places large orders and deposits more collateral when needed.

    This bot focuses on testing the system's behavior with large deposits
    and orders that may require additional collateral.
    """

    # Probability of preparing additional collateral when deposit fails.
    p_prepare_collateral = 0.1

    async def trade(self):
        """
        Execute trading logic for large deposit bot.

        Places orders and handles deposit failures by adding more collateral.
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

            # Submit the order to the exchange.
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
            # Handle Python exceptions like network errors.
            logger.error(f"Exception during order placement: {str(e)}")

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
            or "OMF is less than IMF" in error_message
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
