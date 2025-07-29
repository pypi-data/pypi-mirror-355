"""
Account module with test matchers
"""

import logging
import random
from typing import Optional

from attrs import define
from ddx._rust.common import ProductSymbol
from ddx._rust.common.enums import OrderSide, OrderType
from ddx._rust.decimal import Decimal
from tests.harness.matchers.account import AccountMatcher

logger = logging.getLogger(__name__)


@define
class FuzzedAccountMatcher(AccountMatcher):
    """
    Defines a FuzzedAccountMatcher.

    An FuzzedAccountMatcher is an AccountMatcher that can execute fuzzed orders and match their actions with the expected transactions.
    """

    @classmethod
    async def generate_fuzzed_order(
        cls,
        symbol: ProductSymbol,
        strategy: str,
        amount_range: tuple[Decimal, Decimal],
        price_range: tuple[Decimal, Decimal],
        order_type: Optional[OrderType] = None,
    ):
        """
        Generates a fuzzed order to DerivaDEX.

        Parameters
        ----------
        symbol : str
            Symbol name (e.g., 'ETHPERP').
        strategy : str
            Strategy name (only 'main' supported for now).
        amount_range : tuple[Decimal, Decimal]
            Amount range (e.g., (Decimal('0.1'), Decimal('0.2'))).
        price_range : tuple[Decimal, Decimal]
            Price range (e.g., (Decimal('1000'), Decimal('2000'))).
        """

        # Determine price and amount
        amount = Decimal(
            str(
                round(random.uniform(float(amount_range[0]), float(amount_range[1])), 6)
            )
        )
        price = Decimal(
            str(round(random.uniform(float(price_range[0]), float(price_range[1])), 6))
        )

        # Determine side
        side = random.choice([OrderSide.Bid, OrderSide.Ask])

        # Determine order type
        order_type = (
            random.choice([OrderType.Limit, OrderType.Market])
            if order_type is None
            else order_type
        )
        if order_type == OrderType.Market:
            price = Decimal("0")

        return price, amount, side, order_type

    async def should_fuzzed_order(
        self,
        symbol: ProductSymbol,
        strategy: str,
        amount_range: tuple[Decimal, Decimal],
        price_range: tuple[Decimal, Decimal],
    ):
        """
        Should submit a fuzzed order to DerivaDEX.

        Parameters
        ----------
        symbol : str
            Symbol name (e.g., 'ETHPERP').
        strategy : str
            Strategy name (only 'main' supported for now).
        amount_range : tuple[Decimal, Decimal]
            Amount range (e.g., (Decimal('0.1'), Decimal('0.2'))).
        price_range : tuple[Decimal, Decimal]
            Price range (e.g., (Decimal('1000'), Decimal('2000'))).
        """

        (
            price,
            amount,
            side,
            order_type,
        ) = await FuzzedAccountMatcher.generate_fuzzed_order(
            symbol, strategy, amount_range, price_range
        )

        return await self.should_order(
            symbol, strategy, side, order_type, amount, price, Decimal("0")
        )
