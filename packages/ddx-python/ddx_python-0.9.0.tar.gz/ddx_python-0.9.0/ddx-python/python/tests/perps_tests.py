"""
Integration tests module for the perpetual product
"""

import logging
from datetime import datetime

import aiohttp
import pandas as pd
import pytest
from ddx._rust.common import ProductSymbol
from ddx._rust.common.enums import OrderSide, OrderType
from ddx._rust.decimal import Decimal
from tests.harness.account import Account
from tests.harness.market_data_driver.custom_market_data_driver import \
    CustomMarketDataDriver
from tests.harness.matchers.account import AccountMatcher
from tests.harness.matchers.tick import default_match_all_up_to
from tests.harness.store import Store
from tests.python_only import maybe_mock_client

# Perp test parameters --------------------------------------------------------


logger = logging.getLogger(__name__)
# Seed the random number generator with the current date so that the tests are deterministic up to the day.
# If further determinism is needed for debugging a fuzzed test, the seed can be set explicitly.
random_seed = datetime.today().strftime("%Y-%m-%d")
logger.info(f"Random seed: {random_seed}")


@pytest.fixture
def random_seed():
    return random_seed


@pytest.fixture
def symbol():
    return ProductSymbol("ETHP")


@pytest.fixture
def underlying():
    return "ETH/USD"


@pytest.fixture
def symbol_2():
    return ProductSymbol("BTCP")


@pytest.fixture
def underlying_2():
    return "BTC/USD"


# Common tests -----------------------------------------------------------------------


from tests import common_tests


def register_tests():
    all_common_tests = [
        *common_tests.matching.all_tests,
        *common_tests.trade_mining.all_tests,
        *common_tests.liquidation.all_tests,
        *common_tests.pnl_realization.all_tests,
    ]
    for test in all_common_tests:
        globals()[test.__name__] = test


register_tests()


# Specific tests --------------------------------------------------------------------


perp_symbol = symbol
perp_symbol_2 = symbol_2


@pytest.mark.asyncio
async def test_funding_payments(perp_symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {perp_symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-04-18"),
                duration="1m",
                price_ranges={perp_symbol: (Decimal("100"), Decimal("200"))},
            ),
            client,
        ) as tick_generator:
            # Alice deposits 10_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("10_000"))

            # Bob deposits 10_000 USDC.
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("10_000"))

            # The index price and mark price begin at 100.

            # Alice submits her first order (post).
            await alice.should_post_order(
                perp_symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("1.0"),
                Decimal("100"),
                Decimal("0"),
            )

            # Bob submits his first order (match - complete fill).
            # Alice successfully opens a long position of 1 <perp_symbol> for an entry price of 100 USDC. Bob successfully opens a short position of 1 <perp_symbol> for an entry price of 100 USDC.
            # They both have an unrealized pnl of 0.
            # Bob's order incurs a taker fee, and so his collateral reduces to 10_000 - 0.002 * 1.0 * 100 = 9_999.8.
            await bob.should_complete_fill_order(
                perp_symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("1.0"),
                Decimal("100"),
                Decimal("0"),
            )

            # Bob submits his second order (post). This is the ensure the mark price is initialized to 100 so that there is a nonzero funding rate.
            await bob.should_post_order(
                perp_symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("0.1"),
                Decimal("100"),
                Decimal("0"),
            )

            # Now, the index price moves to 200. The mark price here is 199.
            # The mark price is lower than the index price, resulting in a negative funding rate. Thus, the shorts pay the longs and it is reflected in the avaiable collateral.
            current = await default_match_all_up_to(
                store.advance_until_next_funding_period(tick_generator)
            )

            current.should_advance_settlement_epoch_with_funding()
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. realized pnl and funding payment updates to strategies).


@pytest.mark.asyncio
async def test_funding_payments_no_funding_rate(perp_symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {perp_symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-04-18"),
                duration="1m",
                price_ranges={perp_symbol: (Decimal("2_000"), Decimal("2_000.5"))},
            ),
            client,
        ) as tick_generator:
            # Alice deposits 10_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("10_000"))

            # Bob deposits 10_000 USDC.
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("10_000"))

            # The index price and mark price begin at 2_000.

            # Alice submits her first order (post).
            await alice.should_post_order(
                perp_symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("1.0"),
                Decimal("2_000"),
                Decimal("0"),
            )

            # Bob submits his first order (match - complete fill).
            # Alice successfully opens a long position of 1 <perp_symbol> for an entry price of 2_000 USDC. Bob successfully opens a short position of 1 <perp_symbol> for an entry price of 2_000 USDC.
            # They both have an unrealized pnl of 0.
            # Bob's order incurs a taker fee, and so his collateral reduces to 10_000 - 0.002 * 1.0 * 2_000 = 9_996.
            await bob.should_complete_fill_order(
                perp_symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("1.0"),
                Decimal("2_000"),
                Decimal("0"),
            )

            # Bob submits his second order (post). This is the ensure the mark price is initialized to 2_000. Note however, that the funding rate will be 0.
            await bob.should_post_order(
                perp_symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("0.1"),
                Decimal("2_000"),
                Decimal("0"),
            )

            # Now, the index price moves to 2_000.05. The mark price here is 2_000.38023.
            # There is not a substantial enough difference between the index price and the mark price, resulting in a zero funding rate.
            current = await default_match_all_up_to(
                store.advance_until_next_funding_period(tick_generator)
            )

            current.should_advance_settlement_epoch_with_funding()
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. realized pnl and funding payment updates to strategies).


@pytest.mark.asyncio
async def test_funding_payments_insolvency(perp_symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {perp_symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-04-18"),
                duration="2m",
                price_ranges={perp_symbol: (Decimal("2_000"), Decimal("1_400"))},
            ),
            client,
        ) as tick_generator:
            # Alice deposits 1_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("1_015"))

            # Bob deposits 5_000 USDC.
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("5_000"))

            # The index price and mark price begin at 2_000.

            # Alice submits her first order (post).
            await alice.should_post_order(
                perp_symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("1.5"),
                Decimal("2_000"),
                Decimal("0"),
            )

            # Bob submits his first order (match - complete fill).
            # Alice successfully opens a long position of 1.5 <perp_symbol> for an entry price of 2_000 USDC. Bob successfully opens a short position of 1.5 <perp_symbol> for an entry price of 2_000 USDC.
            # They both have an unrealized pnl of 0.
            # Bob's order incurs a taker fee, and so his collateral reduces to 5_000 - 0.002 * 1.5 * 2_000 = 4_994.
            # Alice has a margin fraction (mf) of 1_015 / (1.5 * 2_000) = 0.3383. Bob has an mf of 4_994 / (1.5 * 2_000) = 1.6647.
            await bob.should_complete_fill_order(
                perp_symbol,
                "main",
                OrderSide.Ask,
                OrderType.Market,
                Decimal("1.5"),
                Decimal("0"),
                Decimal("0"),
            )

            # Bob submits his second order (post). This is the ensure the mark price is initialized to 2_000.
            await bob.should_post_order(
                perp_symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("0.1"),
                Decimal("2_000"),
                Decimal("0"),
            )

            # Now, the index price moves to 1_700. The mark price here is 1_708.5.
            # The mark price is higher than the index price, resulting in a positive funding rate. Thus, the longs pay the shorts and it is reflected in the avaiable collateral.
            # Alice's available collateral ends up being 1002.186250 and Bob's avaiable collateral ends up being 5006.813750 after funding payments.
            # Alice's mf is 1002.186250 / (1.5 * 1_708.5) = 0.3911.
            # Bob's mf is 5006.813750 / (1.5 * 1_708.5) = 1.9537.
            # We're all good (so far).
            current = await default_match_all_up_to(
                store.advance_until_next_funding_period(tick_generator)
            )

            current.should_advance_settlement_epoch_with_funding()
            current.default_match_rest()

            # Now, the index price moves to 1_400. The mark price here is 1_407.
            # Unrealized pnl becomes realized here. Alice now has a realized pnl of -889.5. Bob has a realized pnl of +889.5. Alice now has a available collateral balance of 112.686250. Bob has a available collateral balance of 5_896.313750.
            # (Note that realizing pnl cannot result in liquidations, because if realizing pnl did cause a liquidation, it would have been caught earlier in processing a new index price and the liquidation would have been triggered then. Alice's mf is 112.686250 / (1.5 * 1_407) = 0.05339. Bob's mf is 5_896.313750 / (1.5 * 1_407) = 2.7938. We're good, but...)
            # The mark price is higher than the index price, resulting in a positive funding rate. Thus, the longs pay the shorts and it is reflected in the avaiable collateral.
            # Alice's available collateral ends up being 102.133750 and Bob's avaiable collateral ends up being 5906.866250 after funding payments.
            # Alice's mf is 102.133750 / (1.5 * 1_407) = 0.04839 (uh-oh!)
            # Bob's mf is 5_906.866250 / (1.5 * 1_407) = 2.7988.
            # Alice's mf is lower than the maintenance margin fraction (mmf) of 0.05! Alice will get liquidated.
            # Alice's bankruptcy price is 1_407 - 102.133750 / 1.5 = 1_338.9109. This mark price is the point at which Alice's total value of her positions is 0 (her unrealized pnl at this point would be -102.133750, so her total value at this point would be 102.133750 - 102.133750 = 0).
            # Alice's position is attempted to be sold to the open market as a market order ask. However, there are no bids in the book and there remains a full balance of 1.5 <perp_symbol> on the liquidated position. Thus, the exchange starts ADL'ing other positions by highest unrealized pnl first, position key second. However, in this case, there is only one position, Bob's short of 1.5 <perp_symbol>.
            # Bob's long position is automatically closed by the exchange at the bankruptcy price of 1_338.9109. Alice's realized pnl from her liquidated position is -102.133750, and her collateral after Bob's position is closed is 102.133750 - 102.133750 = 0. Bob's realized pnl from his closed position is 102.133750, and his collateral after his position is closed is 5_906.866250 + 102.133750 = 6_009.
            # Since Alice's collateral at this point is 0, she has been fully liquidated. Bob has also been ADL'd and his long position closed by the exchange.
            current = await default_match_all_up_to(
                store.advance_until_next_funding_period(tick_generator)
            )

            current.should_advance_settlement_epoch_with_funding()
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. realized pnl and funding payment updates to strategies).


@pytest.mark.asyncio
async def test_mul_funding_payments(perp_symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {perp_symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-04-18"),
                duration="2m",
                price_ranges={perp_symbol: (Decimal("100"), Decimal("300"))},
            ),
            client,
        ) as tick_generator:
            # Alice deposits 1_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("1_000"))

            # Bob deposits 10_000 USDC.
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("10_000"))

            # The index price and mark price begin at 100.

            # Alice submits her first order (post).
            await alice.should_post_order(
                perp_symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("0.1"),
                Decimal("100"),
                Decimal("0"),
            )

            # Bob submits his first order (match - complete fill).
            # Alice successfully opens a long position of 0.1 <perp_symbol> for an entry price of 100 USDC. Bob successfully opens a short position of 1 <perp_symbol> for an entry price of 100 USDC.
            # They both have an unrealized pnl of 0.
            # Bob's order incurs a taker fee, and so his collateral reduces to 10_000 - 0.002 * 0.1 * 100 = 9_999.98.
            await bob.should_complete_fill_order(
                perp_symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("0.1"),
                Decimal("100"),
                Decimal("0"),
            )

            # Bob submits his second order (post). This is the ensure the mark price is initialized to 100.
            await bob.should_post_order(
                perp_symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("0.1"),
                Decimal("100"),
                Decimal("0"),
            )

            # Now, the index price moves to 200. The mark price here is 199.
            # The mark price is lower than the index price, resulting in a negative funding rate. Thus, the shorts pay the longs and it is reflected in the avaiable collateral.
            # Alice's avaiable collateral ends up being 1_000.0995 and Bob's avaiable collateral ends up being 9_999.8805 after funding payments.
            current = await default_match_all_up_to(
                store.advance_until_next_funding_period(tick_generator)
            )
            current.should_advance_settlement_epoch_with_funding()
            current.default_match_rest()

            # Now, the index price moves to 300. The mark price here is 298.5.
            # Alice now has a realized pnl of +19.85. Bob has a realized pnl of -19.85. Alice now has a avaiable collateral balance of 1_019.9495. Bob has a avaiable collateral balance of 9_980.0305.
            # The mark price is lower than the index price, resulting in a negative funding rate. Thus, the shorts pay the longs and it is reflected in the avaiable collateral.
            # Alice's avaiable collateral ends up being 1_020.09875 and Bob's avaiable collateral ends up being 9_979.88125 after funding payments.
            current = await default_match_all_up_to(
                store.advance_until_next_funding_period(tick_generator)
            )

            current.should_advance_settlement_epoch_with_funding()
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. realized pnl and funding payment updates to strategies).


@pytest.mark.asyncio
async def test_funding_payments_mul_symbols(
    perp_symbol, underlying, perp_symbol_2, underlying_2
):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {perp_symbol: underlying, perp_symbol_2: underlying_2},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-04-18"),
                duration="1m",
                price_ranges={
                    perp_symbol: (Decimal("100"), Decimal("500")),
                    perp_symbol_2: (Decimal("200"), Decimal("500")),
                },
            ),
            client,
        ) as tick_generator:
            # Alice deposits 10_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("10_000"))

            # Bob deposits 10_000 USDC.
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("10_000"))

            # The index price and mark price begin at 100.

            # Alice submits her first order (post).
            await alice.should_post_order(
                perp_symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("0.1"),
                Decimal("100"),
                Decimal("0"),
            )

            # Bob submits his first order (match - complete fill).
            # Alice successfully opens a long position of 0.1 <perp_symbol> for an entry price of 100 USDC. Bob successfully opens a short position of 0.1 <perp_symbol> for an entry price of 100 USDC.
            # They both have an unrealized pnl of 0.
            # Bob's order incurs a taker fee, and so his collateral reduces to 10_000 - 0.002 * 0.1 * 100 = 9_999.98.
            await bob.should_complete_fill_order(
                perp_symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("0.1"),
                Decimal("100"),
                Decimal("0"),
            )

            # Alice submits her second order (post).
            await alice.should_post_order(
                perp_symbol_2,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("1"),
                Decimal("200"),
                Decimal("0"),
            )

            # Bob submits his second order (match - complete fill).
            # Alice successfully opens a long position of 1 <perp_symbol_2> for an entry price of 200 USDC. Bob successfully opens a short position of 1 <perp_symbol_2> for an entry price of 200 USDC.
            # They both have an unrealized pnl of 0.
            # Bob's order incurs a taker fee, and so his collateral reduces to 9_999.98 - 0.002 * 1 * 200 = 9_999.58.
            await bob.should_complete_fill_order(
                perp_symbol_2,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("1"),
                Decimal("200"),
                Decimal("0"),
            )

            # Bob submits his third and fourth orders (post). This is the ensure the mark prices are initialized to 100 and 200 respectively.
            await bob.should_post_order(
                perp_symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("0.1"),
                Decimal("100"),
                Decimal("0"),
            )

            await bob.should_post_order(
                perp_symbol_2,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("1"),
                Decimal("200"),
                Decimal("0"),
            )

            # Now, both index prices move to 500. Both mark prices here are 497.50.
            # The mark price is lower than the index price, resulting in a negative funding rate. Thus, the shorts pay the longs and it is reflected in the avaiable collateral.
            # Alice's avaiable collateral ends up being 10_002.736250 and Bob's avaiable collateral ends up being 9_996.843750 after funding payments.
            current = await default_match_all_up_to(
                store.advance_until_next_funding_period(tick_generator)
            )

            current.should_advance_settlement_epoch_with_funding()
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. realized pnl and funding payment updates to strategies).
