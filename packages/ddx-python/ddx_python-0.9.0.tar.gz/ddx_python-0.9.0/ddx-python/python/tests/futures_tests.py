"""
Integration tests module for the future product
"""

import logging
from datetime import datetime, timezone

import aiohttp
import numpy as np
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

# Future test parameters --------------------------------------------------------


logger = logging.getLogger(__name__)
# Seed the random number generator with the current date so that the tests are deterministic up to the day.
# If further determinism is needed for debugging a fuzzed test, the seed can be set explicitly.
random_seed = datetime.today().strftime("%Y-%m-%d")
logger.info(f"Random seed: {random_seed}")

MARCH_EXPIRY_DATETIME = datetime(2024, 3, 29, 8, 0, 0, 0, timezone.utc)


@pytest.fixture
def random_seed():
    return random_seed


@pytest.fixture
def symbol():
    return ProductSymbol("ETHFH")


@pytest.fixture
def underlying():
    return "ETH/USD"


@pytest.fixture
def symbol_2():
    return ProductSymbol("BTCFH")


@pytest.fixture
def underlying_2():
    return "BTC/USD"


@pytest.fixture
def perp_symbol():
    return ProductSymbol("BTCP")


@pytest.fixture
def perp_underlying():
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


future_symbol = symbol
future_symbol_2 = symbol_2


@pytest.mark.asyncio
async def test_futures_expiry(future_symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {future_symbol: underlying},
                "10s",
                client,
                # Last Friday of March 2024, 1 minute before expiry
                start_timestamp=pd.Timestamp("2024-03-29T07:59:00"),
                duration="1min",
                price_ranges={future_symbol: (Decimal("100"), Decimal("200"))},
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
                future_symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("1.0"),
                Decimal("100"),
                Decimal("0"),
            )

            # Bob submits his first order (match - complete fill).
            # Alice successfully opens a long position of 1 <future_symbol> for an entry price of 100 USDC. Bob successfully opens a short position of 1 <future_symbol> for an entry price of 100 USDC.
            # They both have an unrealized pnl of 0.
            # Bob's order incurs a taker fee, and so his collateral reduces to 10_000 - 0.002 * 1.0 * 100 = 9_999.8.
            await bob.should_complete_fill_order(
                future_symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("1.0"),
                Decimal("100"),
                Decimal("0"),
            )

            # Bob submits his second order (post). This is to ensure the mark price is initialized to 100.
            await bob.should_post_order(
                future_symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("0.1"),
                Decimal("100"),
                Decimal("0"),
            )

            # Now, the index price moves to 200. For the delivery price duration before expiry (in tests, 20 seconds), the mark price calculation forgoes the EMA and uses the running average as the mark price and so at expiry the mark price here is the running average over the delivery price duration, which is 183.333333.
            # Unrealized pnl becomes realized. Alice now has a realized pnl of +83.333333. Bob has a realized pnl of -83.333333. Alice now has a available collateral balance of 10_083.333333. Bob has a available collateral balance of 9_916.466667.
            # In addition to unrealized pnl becoming realized, the <future_symbol> futures contract expires.
            # Alice and Bob's <future_symbol> positions are both closed at the delivery price of 183.333333.
            current = await default_match_all_up_to(
                store.advance_until_time(tick_generator, MARCH_EXPIRY_DATETIME)
            )

            current.should_advance_settlement_epoch_with_futures_expiry()
            current.should_update_product_listings_with_removals()
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. realized pnl and funding payment updates to strategies).


@pytest.mark.asyncio
async def test_list_next_future(future_symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {future_symbol: underlying},
                "10s",
                client,
                # Second-to-last Friday of March 2024, exactly 1 week and 30 seconds before expiry
                start_timestamp=pd.Timestamp("2024-03-22T07:59:30"),
                duration="30s",
                price_ranges={future_symbol: (Decimal("100"), Decimal("200"))},
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
                future_symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("1.0"),
                Decimal("100"),
                Decimal("0"),
            )

            # Bob submits his first order (match - complete fill).
            # Alice successfully opens a long position of 1 <future_symbol> for an entry price of 100 USDC. Bob successfully opens a short position of 1 <future_symbol> for an entry price of 100 USDC.
            # They both have an unrealized pnl of 0.
            # Bob's order incurs a taker fee, and so his collateral reduces to 10_000 - 0.002 * 1.0 * 100 = 9_999.8.
            await bob.should_complete_fill_order(
                future_symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("1.0"),
                Decimal("100"),
                Decimal("0"),
            )

            # Bob submits his second order (post). This is to ensure the mark price is initialized to 100.
            await bob.should_post_order(
                future_symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("0.1"),
                Decimal("100"),
                Decimal("0"),
            )

            # We advance to exactly one week before expiry. There should be an listing addition of the futures contract expiring three quarters from now.
            current = await default_match_all_up_to(
                store.advance_until_time(
                    tick_generator, datetime(2024, 3, 22, 8, 0, 0, 0, timezone.utc)
                )
            )

            current.should_update_product_listings_with_additions()
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. realized pnl and funding payment updates to strategies).


@pytest.mark.asyncio
async def test_futures_expiry_liquidate_no_adl_on_mark_price_discontinuity(
    future_symbol, underlying
):
    # Last Friday of March 2024, 1 minute before expiry
    start_timestamp = pd.Timestamp("2024-03-29T07:59:00")
    end_timestamp = pd.Timestamp("2024-03-29T08:00:00")
    timestamps = (
        pd.date_range(
            start=start_timestamp,
            end=end_timestamp - pd.Timedelta("20s"),
            freq="10s",
        )[:-1],
        pd.date_range(
            start=end_timestamp - pd.Timedelta("20s"),
            end=end_timestamp,
            freq="10s",
        ),
    )
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver(
                {future_symbol: underlying},
                start_timestamp,
                "10s",
                client,
                {
                    future_symbol: timestamps[0].union(timestamps[1]),
                },
                {
                    future_symbol: [Decimal("2_000")] * len(timestamps[0])
                    + [Decimal("1_375")] * len(timestamps[1])
                },
            ),
            client,
        ) as tick_generator:
            # Alice deposits 1_015 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("1_015"))

            # Bob deposits 5_000 USDC.
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("5_000"))

            # Charlie deposits 10_000 USDC.
            charlie = AccountMatcher(Account(store.wallet.account_for_index(2)))
            await charlie.should_deposit("main", Decimal("10_000"))

            # The index price and mark price begin at 2_000.

            # Alice submits her first order (post).
            await alice.should_post_order(
                future_symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("1.5"),
                Decimal("2_000"),
                Decimal("0"),
            )

            # Bob submits his first order (match - complete fill).
            # Alice successfully opens a long position of 1.5 <future_symbol> for an entry price of 2_000 USDC. Bob successfully opens a short position of 1.5 <future_symbol> for an entry price of 2_000 USDC.
            # They both have an unrealized pnl of 0.
            # Bob's order incurs a taker fee, and so his collateral reduces to 5_000 - 0.002 * 1.5 * 2_000 = 4_994.
            # Alice has a margin fraction (mf) of 1_015 / (1.5 * 2_000) = 0.3383. Bob has an mf of 4_994 / (1.5 * 2_000) = 1.6647.
            await bob.should_complete_fill_order(
                future_symbol,
                "main",
                OrderSide.Ask,
                OrderType.Market,
                Decimal("1.5"),
                Decimal("0"),
                Decimal("0"),
            )

            # Charlie submits his first order (post). This is to ensure no ADL occurs.
            await charlie.should_post_order(
                future_symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("1.5"),
                Decimal("1_375"),
                Decimal("0"),
            )

            # At 20 seconds before expiry, the delivery price duration before expiry, the index price jumps to 1_375. Since at exactly this tick the mark price calculation forgoes the EMA and starts using the running average as the mark price, on this tick the mark price is exactly the index price, which is 1_375. That is, the mark price on tick x - 1 and x where x is 20 seconds before expiry is 2_000 and 1_375 respectively.
            # The unrealized pnl for the previous settlement epoch was 0 for both Alice and Bob.
            # At this 20 second mark, as part of the processing of a new index price, the solvency of strategies is checked. Alice's mf is (1_015 - 937.5) / (1.5 * 1_375) = 0.037576 where -937.5 is the unrealized pnl at this point (uh-oh!).
            # Bob's position is the other side, and so his mf doesn't matter.
            # Charlie has no positions, so his mf doesn't matter.
            # Alice's mf is lower than the maintenance margin fraction (mmf) of 0.05! Alice will get liquidated.
            # Alice's bankruptcy price (of <future_symbol>) is 1_375 - (1_015 - 937.5) / 1.5 = 1_323.333333. This mark price is the point at which Alice's total value of her positions is 0 (her unrealized pnl at this point would be -(1_015 - 937.5) = -77.5, so her total value at this point would be 77.5 - 77.5 = 0).
            # Alice's position is attempted to be sold to the open market as a market order ask. Her taker, Charlie, gets filled at the full amount of 1.5 @ 1_375.
            # The exchange is lucky here, as there is a positive price delta from this trade, 1_375 - 1_323.333333 = 51.666667, meaning that after filling the trade 1.5 @ 1_375, there will still be USDC left in the account that will go to the insurance fund. Namely, 51.666667 * 1.5 = 77.500005 will go to the organic insurance fund.
            # The main criteria that was checked here was `insurance_fund_cap + liquidation_spread >= 0`, where `liquidation_spread = price_delta * fill_amount`. Here, liquidation_spread was positive since price_delta was positive, meaning that the exchange profited from the liquidation sale. Thus, insurance funds were not needed and were instead added to. However, if the liquidation_spread were negative (due to the price_delta being negative), funds from the organic insurance fund would be needed to cover losses on an immediate liquidation sale, subject to the above nonnegativity constraint. To satisfy this constraint it is sufficient to clamp the possible_fill_amount with a max fill amount of `insurance_fund_cap / |price_delta|` or less. For more details, see `derivadex/rust-packages/ddx-operator/enclave/src/execution/liquidation.rs`.
            # Finally, note that the fill amount undergoes a final check, Charlie's solvency guard, and Charlie successfully opens a long position of 1.5 <future_symbol> for an entry price of 1_375 USDC because Charlie's collateral is enough so that after the trade, Charlie's mf 10_000 / (1.5 * 1_375) = 4.848484 of is solvent.
            # Alice's collateral at this point is 1_015 - 1_015 = 0. She has been fully liquidated. Bob's collateral at this point is still 4_994. Charlie's collateral at this point is 10_000.

            # At this point, ticks continue to be processed as normal. There are two positions when <future_symbol> finally expires at a delivery price of 1_375.
            # Unrealized pnl becomes realized here. Bob now has a realized pnl of +937.5. Charlie has a realized pnl of 0. Bob now has a available collateral balance of 5_931.5. Bob has a available collateral balance of 10_000.
            # In addition to unrealized pnl becoming realized, the <future_symbol> futures contract expires, as it has been 240s since the contract was created.
            # Alice and Bob's <future_symbol> positions are both closed at the delivery price of 1_375.
            current = await default_match_all_up_to(
                store.advance_until_time(tick_generator, MARCH_EXPIRY_DATETIME)
            )

            current.should_advance_settlement_epoch_with_futures_expiry()
            current.should_update_product_listings_with_removals()
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. realized pnl and funding payment updates to strategies).


@pytest.mark.asyncio
async def test_futures_expiry_liquidate_with_adl_on_mark_price_discontinuity(
    future_symbol, underlying
):
    # Last Friday of March 2024, 1 minute before expiry
    start_timestamp = pd.Timestamp("2024-03-29T07:59:00")
    end_timestamp = pd.Timestamp("2024-03-29T08:00:00")
    timestamps = (
        pd.date_range(
            start=start_timestamp,
            end=end_timestamp - pd.Timedelta("20s"),
            freq="10s",
        )[:-1],
        pd.date_range(
            start=end_timestamp - pd.Timedelta("20s"),
            end=end_timestamp,
            freq="10s",
        ),
    )
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver(
                {future_symbol: underlying},
                start_timestamp,
                "10s",
                client,
                {
                    future_symbol: timestamps[0].union(timestamps[1]),
                },
                {
                    future_symbol: [Decimal("2_000")] * len(timestamps[0])
                    + [Decimal("1_375")] * len(timestamps[1])
                },
            ),
            client,
        ) as tick_generator:
            # Alice deposits 10_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("1_015"))

            # Bob deposits 10_000 USDC.
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("5_000"))

            # The index price and mark price begin at 2_000.

            # Alice submits her first order (post).
            await alice.should_post_order(
                future_symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("1.5"),
                Decimal("2_000"),
                Decimal("0"),
            )

            # Bob submits his first order (match - complete fill).
            # Alice successfully opens a long position of 1.5 <future_symbol> for an entry price of 2_000 USDC. Bob successfully opens a short position of 1.5 <future_symbol> for an entry price of 2_000 USDC.
            # They both have an unrealized pnl of 0.
            # Bob's order incurs a taker fee, and so his collateral reduces to 5_000 - 0.002 * 1.5 * 2_000 = 4_994.
            # Alice has a margin fraction (mf) of 1_015 / (1.5 * 2_000) = 0.3383. Bob has an mf of 4_994 / (1.5 * 2_000) = 1.6647.
            await bob.should_complete_fill_order(
                future_symbol,
                "main",
                OrderSide.Ask,
                OrderType.Market,
                Decimal("1.5"),
                Decimal("0"),
                Decimal("0"),
            )

            # Bob submits his second order (post). This is to ensure the mark price is initialized to 2_000.
            await bob.should_post_order(
                future_symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("0.1"),
                Decimal("2_000"),
                Decimal("0"),
            )

            # At 20 seconds before expiry, the delivery price duration before expiry, the index price jumps to 1_375. Since at exactly this tick the mark price calculation forgoes the EMA and starts using the running average as the mark price, on this tick the mark price is exactly the index price, which is 1_375. That is, the mark price on tick x - 1 and x where x is 20 seconds before expiry is 2_000 and 1_375 respectively.
            # The unrealized pnl for the previous settlement epoch was 0 for both Alice and Bob.
            # At this 20 second mark, as part of the processing of a new index price, the solvency of strategies is checked. Alice's mf is (1_015 - 937.5) / (1.5 * 1_375) = 0.037576 where -937.5 is the unrealized pnl at this point (uh-oh!).
            # Bob's position is the other side, and so his mf doesn't matter.
            # Alice's mf is lower than the maintenance margin fraction (mmf) of 0.05! Alice will get liquidated.
            # Alice's bankruptcy price (of <future_symbol>) is 1_375 - (1_015 - 937.5) / 1.5 = 1_323.333333. This mark price is the point at which Alice's total value of her positions is 0 (her unrealized pnl at this point would be -(1_015 - 937.5) = -77.5, so her total value at this point would be 77.5 - 77.5 = 0).
            # Alice's position is attempted to be sold to the open market as a market order ask. However, there are no bids in the book and there remains a full balance of 1.5 <future_symbol> on the liquidated position. Thus, the exchange starts ADL'ing other positions by highest unrealized pnl first, position key second. However, in this case, there is only one position, Bob's short of 1.5 <future_symbol>.
            # Bob's long position is automatically closed by the exchange at the bankruptcy price of 1_323.333333. Alice's realized pnl from her liquidated position is -1_015, and her collateral after Bob's position is closed is 1_015 - 1_015 = 0. Bob's realized pnl from his closed position is 1_015, and his collateral after his position is closed is 4_994 + 1_015 = 6_009.
            # Since Alice's collateral at this point is 0, she has been fully liquidated. Bob has also been ADL'd and his short position closed by the exchange.

            # At this point, ticks continue to be processed as normal. There are no more positions when <future_symbol> finally expires at a delivery price of 1_375.
            current = await default_match_all_up_to(
                store.advance_until_time(tick_generator, MARCH_EXPIRY_DATETIME)
            )

            current.should_advance_settlement_epoch_with_futures_expiry()
            current.should_update_product_listings_with_removals()
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. realized pnl and funding payment updates to strategies).


@pytest.mark.asyncio
async def test_futures_expiry_liquidate_with_adl_on_adjusted_mark_price(
    future_symbol, underlying
):
    # Last Friday of March 2024, 1 minute before expiry
    start_timestamp = pd.Timestamp("2024-03-29T07:59:00")
    end_timestamp = pd.Timestamp("2024-03-29T08:00:00")
    timestamps = (
        pd.date_range(
            start=start_timestamp,
            end=end_timestamp - pd.Timedelta("20s"),
            freq="10s",
        )[:-1],
        pd.date_range(
            start=end_timestamp - pd.Timedelta("20s"),
            end=end_timestamp,
            freq="10s",
        ),
    )
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver(
                {future_symbol: underlying},
                start_timestamp,
                "10s",
                client,
                {
                    future_symbol: timestamps[0].union(timestamps[1]),
                },
                {
                    future_symbol: [Decimal("2_000")] * len(timestamps[0])
                    + list(
                        np.linspace(
                            float(Decimal("1_400")),
                            float(Decimal("1_375")),
                            len(timestamps[1]),
                        ).round(6)
                    )
                },
            ),
            client,
        ) as tick_generator:
            # Alice deposits 10_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("1_015"))

            # Bob deposits 10_000 USDC.
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("5_000"))

            # The index price and mark price begin at 2_000.

            # Alice submits her first order (post).
            await alice.should_post_order(
                future_symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("1.5"),
                Decimal("2_000"),
                Decimal("0"),
            )

            # Bob submits his first order (match - complete fill).
            # Alice successfully opens a long position of 1.5 <future_symbol> for an entry price of 2_000 USDC. Bob successfully opens a short position of 1.5 <future_symbol> for an entry price of 2_000 USDC.
            # They both have an unrealized pnl of 0.
            # Bob's order incurs a taker fee, and so his collateral reduces to 5_000 - 0.002 * 1.5 * 2_000 = 4_994.
            # Alice has a margin fraction (mf) of 1_015 / (1.5 * 2_000) = 0.3383. Bob has an mf of 4_994 / (1.5 * 2_000) = 1.6647.
            await bob.should_complete_fill_order(
                future_symbol,
                "main",
                OrderSide.Ask,
                OrderType.Market,
                Decimal("1.5"),
                Decimal("0"),
                Decimal("0"),
            )

            # Bob submits his second order (post). This is to ensure the mark price is initialized to 2_000.
            await bob.should_post_order(
                future_symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("0.1"),
                Decimal("2_000"),
                Decimal("0"),
            )

            # At 20 seconds before expiry, the delivery price duration before expiry, the index price jumps to 1_400. Since at exactly this tick the mark price calculation forgoes the EMA and starts using the running average as the mark price, on this tick the mark price is exactly the index price, which is 1_400. That is, the mark price on tick x - 1 and x where x is 20 seconds before expiry is 2_000 and 1_400 respectively.
            # The unrealized pnl for the previous settlement epoch was 0 for both Alice and Bob.
            # At this 20 second mark, as part of the processing of a new index price, the solvency of strategies is checked. Alice's mf is (1_015 - 900) / (1.5 * 1_400) = 0.054761 where -900 is the unrealized pnl at this point. Alice is good (so far).
            # Bob's position is the other side, and so his mf doesn't matter.

            # At this point, ticks continue to be processed as normal. However, an index price of 1_375 comes in, and the running average (and mark price) at this point becomes 1_387.5.
            # As normal, the solvency of strategies is checked. Alice's mf is (1_015 - 918.75) / (1.5 * 1_387.5) = 0.046246 where -918.75 is the unrealized pnl at this point (uh-oh!).
            # Bob's position is the other side, and so his mf doesn't matter.
            # Alice's mf is lower than the maintenance margin fraction (mmf) of 0.05! Alice will get liquidated.
            # Alice's bankruptcy price (of <future_symbol>) is 1_387.5 - (1_015 - 918.75) / 1.5 = 1_323.333333. This mark price is the point at which Alice's total value of her positions is 0 (her unrealized pnl at this point would be -(1_015 - 918.75) = -96.25, so her total value at this point would be 96.25 - 96.25 = 0).
            # Alice's position is attempted to be sold to the open market as a market order ask. However, there are no bids in the book and there remains a full balance of 1.5 <future_symbol> on the liquidated position. Thus, the exchange starts ADL'ing other positions by highest unrealized pnl first, position key second. However, in this case, there is only one position, Bob's short of 1.5 <future_symbol>.
            # Bob's long position is automatically closed by the exchange at the bankruptcy price of 1_323.333333. Alice's realized pnl from her liquidated position is -1_015, and her collateral after Bob's position is closed is 1_015 - 1_015 = 0. Bob's realized pnl from his closed position is 1_015, and his collateral after his position is closed is 4_994 + 1_015 = 6_009.
            # Since Alice's collateral at this point is 0, she has been fully liquidated. Bob has also been ADL'd and his short position closed by the exchange.
            # This is also a settlement epoch tick, and more importantly a futures expiry tick. But all <future_symbol> positions are closed, so there is nothing to expire. There is also no more pnl to realize since there are no positions.
            current = await default_match_all_up_to(
                store.advance_until_time(tick_generator, MARCH_EXPIRY_DATETIME)
            )

            current.should_advance_settlement_epoch_with_futures_expiry()
            current.should_update_product_listings_with_removals()
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. realized pnl and funding payment updates to strategies).


@pytest.mark.asyncio
async def test_futures_expiry_mul_symbols_and_perp(
    future_symbol,
    underlying,
    future_symbol_2,
    underlying_2,
    perp_symbol,
    perp_underlying,
):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {
                    future_symbol: underlying,
                    future_symbol_2: underlying_2,
                    perp_symbol: perp_underlying,
                },
                "10s",
                client,
                start_timestamp=pd.Timestamp("2024-03-29T07:56:00"),
                duration="4min",
                price_ranges={
                    future_symbol: (Decimal("100"), Decimal("200")),
                    future_symbol_2: (Decimal("200"), Decimal("300")),
                    perp_symbol: (Decimal("500"), Decimal("700")),
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

            # The index price and mark price for <future_symbol> begin at 100. The index price and mark price for <future_symbol_2> begin at 200. The index price and mark price for <perp_symbol> begin at 500.

            # Alice submits her first order (post).
            await alice.should_post_order(
                future_symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("1.0"),
                Decimal("100"),
                Decimal("0"),
            )

            # Bob submits his first order (match - complete fill).
            # Alice successfully opens a long position of 1 <future_symbol> for an entry price of 100 USDC. Bob successfully opens a short position of 1 <future_symbol> for an entry price of 100 USDC.
            # They both have an unrealized pnl of 0.
            # Bob's order incurs a taker fee, and so his collateral reduces to 10_000 - 0.002 * 1.0 * 100 = 9_999.8.
            await bob.should_complete_fill_order(
                future_symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("1.0"),
                Decimal("100"),
                Decimal("0"),
            )

            # Bob submits his second order (post).
            await bob.should_post_order(
                future_symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("0.1"),
                Decimal("100"),
                Decimal("0"),
            )

            # Alice submits her second order (post). This is to ensure the mark price of <future_symbol> is initialized to 100.
            await alice.should_post_order(
                future_symbol_2,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("1.0"),
                Decimal("200"),
                Decimal("0"),
            )

            # Bob submits his third order (match - complete fill).
            await bob.should_complete_fill_order(
                future_symbol_2,
                "main",
                OrderSide.Bid,
                OrderType.Market,
                Decimal("1.0"),
                Decimal("0"),
                Decimal("0"),
            )

            # Alice submits her third order (post).
            await alice.should_post_order(
                perp_symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("1.0"),
                Decimal("500"),
                Decimal("0"),
            )

            # Bob submits his fourth order (match - complete fill).
            await bob.should_complete_fill_order(
                perp_symbol,
                "main",
                OrderSide.Bid,
                OrderType.Market,
                Decimal("1.0"),
                Decimal("0"),
                Decimal("0"),
            )

            # Alice submits her fourth order (post). This is to ensure the mark price of <perp_symbol> is initialized to 500.
            await alice.should_post_order(
                perp_symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("0.1"),
                Decimal("500"),
                Decimal("0"),
            )

            # The index prices of <future_symbol>, <future_symbol_2>, and <perp_symbol> move to 200, 300, and 700 respectively. The mark price of <perp_symbol> moves to 696.5.
            # For the delivery price duration before expiry (in tests, 20 seconds), the mark price calculation forgoes the EMA and uses the running average as the mark price and so at expiry the mark price here is the running average over the delivery price duration, so for <future_symbol> it is 195.833333 and for <future_symbol_2> it is 295.833333.
            # Before the 5th settlement epoch (the one with the futures expiry), aggregating the realized pnl and funding payments, Alice has a collateral balance of 9_893.295 and Bob has a collateral balance of 10_058.521667.
            # For this settlement epoch, unrealized pnl becomes realized.
            # For <future_symbol> Alice has a realized pnl of 46.583333. Bob has a realized pnl of -46.583333.
            # For <future_symbol_2> Alice has a realized pnl of -45.833333. Bob has a realized pnl of 45.833333.
            # For <perp_symbol> Alice has a realized pnl of -99.500. Bob has a realized pnl of 99.500.
            # For <perp_symbol> Alice has a funding debit of -3.4825. Bob has a funding credit of 3.4825. Both accounts stay solvent
            # In addition to unrealized pnl becoming realized, the <future_symbol> futures contract expires, as it has been 240s since the contract was created.
            # Alice and Bob's <future_symbol> and <future_symbol_2> positions are both closed at the delivery price of 195.833333 and 295.833333 respectively.
            current = await default_match_all_up_to(
                store.advance_until_time(tick_generator, MARCH_EXPIRY_DATETIME)
            )

            current.should_advance_settlement_epoch_with_futures_expiry()
            current.should_update_product_listings_with_removals()
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. realized pnl and funding payment updates to strategies).
