# This is unfortunate but must be done because
# https://pyo3.rs/main/faq#pyo3get-clones-my-field

from ddx._rust.common import TokenSymbol
from ddx._rust.common.state import InsuranceFundContribution, Strategy
from ddx._rust.decimal import Decimal


def update_avail_collateral(strategy: Strategy, symbol: TokenSymbol, amount: Decimal):
    strategy.avail_collateral = strategy.update_avail_collateral(
        symbol,
        amount,
    )


def update_locked_collateral(strategy: Strategy, symbol: TokenSymbol, amount: Decimal):
    strategy.locked_collateral = strategy.update_locked_collateral(
        symbol,
        amount,
    )


def update_avail_balance(
    contribution: InsuranceFundContribution, symbol: TokenSymbol, amount: Decimal
):
    contribution.avail_balance = contribution.update_avail_balance(
        symbol,
        amount,
    )


def update_locked_balance(
    contribution: InsuranceFundContribution, symbol: TokenSymbol, amount: Decimal
):
    contribution.locked_balance = contribution.update_locked_balance(
        symbol,
        amount,
    )
