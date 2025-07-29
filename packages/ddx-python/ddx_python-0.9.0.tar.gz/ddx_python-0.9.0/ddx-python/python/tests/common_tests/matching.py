import random

import aiohttp
import pandas as pd
import pytest
from ddx._rust.common.enums import OrderSide, OrderType, PositionSide
from ddx._rust.decimal import Decimal
from tests.harness.account import Account
from tests.harness.market_data_driver.custom_market_data_driver import \
    CustomMarketDataDriver
from tests.harness.matchers.account import AccountMatcher
from tests.harness.matchers.fuzzed_account import FuzzedAccountMatcher
from tests.harness.matchers.tick import default_match_all_up_to
from tests.harness.store import Store


@pytest.mark.asyncio
async def test_post_entire_order(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("1_000"), Decimal("1_000"))},
            ),
            client,
        ):
            # Alice deposits 1_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("1_000"))

            # Alice submits an order that gets posted to the book.
            await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("3"),
                Decimal("1800"),
                Decimal("0"),
            )


@pytest.mark.asyncio
async def test_post_order_then_modify(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("500"), Decimal("500"))},
            ),
            client,
        ):
            # Alice deposits 10_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("10_000"))

            # Bob deposits 10_000 USDC.
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("10_000"))

            # Alice submits an order that gets posted to the book.
            _, (_, order_hash) = await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("20"),
                Decimal("500"),
                Decimal("0"),
            )

            # Alice modifies her order.
            await alice.should_modify_order(
                order_hash,
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("15"),
                Decimal("550"),
                Decimal("0"),
            )

            # Bob submit his first order (match - partial fill)
            await bob.should_partial_fill_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("20"),
                Decimal("500"),
                Decimal("0"),
            )


@pytest.mark.asyncio
async def test_modify_nonexistent_order(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("500"), Decimal("500"))},
            ),
            client,
        ):
            # Alice deposits 10_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("10_000"))

            # Alice attempts to modify a nonexistent order.
            await alice.should_not_modify_order(
                "0x00000000000000000000000000000000000000000000000000",
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("15"),
                Decimal("550"),
                Decimal("0"),
            )


@pytest.mark.asyncio
async def test_post_order_then_cancel(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("500"), Decimal("500"))},
            ),
            client,
            version_db=["Post", "Cancel", "StrategyUpdate"],
        ):
            # Alice deposits 10_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("10_000"))

            # Alice submits an order that gets posted to the book.
            _, (_, order_hash) = await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("20"),
                Decimal("500"),
                Decimal("0"),
            )

            # Alice cancels her order.
            await alice.should_cancel_order(
                symbol,
                order_hash,
            )


@pytest.mark.asyncio
async def test_cancel_nonexistent_order(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("500"), Decimal("500"))},
            ),
            client,
        ):
            # Alice deposits 10_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("10_000"))

            # Alice attempts to cancel a nonexistent order.
            await alice.should_not_cancel_order(
                symbol,
                "0x00000000000000000000000000000000000000000000000000",
            )


@pytest.mark.asyncio
async def test_match_multiple_orders(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("1_000"), Decimal("1_000"))},
            ),
            client,
            version_db=["PartialFill", "CompleteFill", "Post"],
        ):
            # Alice deposits 10_000 USDC into the main strategy
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("10_000"))

            # Alice deposits 10_000 USDC into the alt strategy
            await alice.should_deposit("alt", Decimal("10_000"))

            # Bob deposits 10_000 USDC
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("10_000"))

            # Alice submits her first order (post).
            await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("1"),
                Decimal("237"),
                Decimal("0"),
            )

            # Bob submit his first order (match - complete fill)
            await bob.should_complete_fill_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("1"),
                Decimal("237"),
                Decimal("0"),
            )

            # Alice submits her second order (post).
            await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("1"),
                Decimal("238"),
                Decimal("0"),
            )

            # Bob submit his second order (match - complete fill)
            await bob.should_complete_fill_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Market,
                Decimal("1"),
                Decimal("0"),
                Decimal("0"),
            )

            # Alice alt strategy submits first order (post).
            await alice.should_post_order(
                symbol,
                "alt",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("1"),
                Decimal("238"),
                Decimal("0"),
            )

            # Alice main strategy submits her third order (match - complete fill)
            await alice.should_complete_fill_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("1"),
                Decimal("238"),
                Decimal("0"),
            )


@pytest.mark.asyncio
async def test_fuzzed_match_multiple_orders(symbol, underlying, random_seed):
    random.seed(random_seed)
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("250"), Decimal("250"))},
            ),
            client,
        ):
            # Alice deposits 10_000 USDC
            alice = FuzzedAccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("10_000"))

            # Bob deposits 10_000 USDC
            bob = FuzzedAccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("10_000"))

            # Charlie deposits 10_000 USDC
            charlie = FuzzedAccountMatcher(Account(store.wallet.account_for_index(2)))
            await charlie.should_deposit("main", Decimal("10_000"))

            price_range = (Decimal("249"), Decimal("251"))
            amount_range = (Decimal("0.01"), Decimal("2"))
            for _ in range(100):
                # Alice submits her order.
                await alice.should_fuzzed_order(
                    symbol,
                    "main",
                    amount_range,
                    price_range,
                )

                # Bob submit his order.
                await bob.should_fuzzed_order(
                    symbol,
                    "main",
                    amount_range,
                    price_range,
                )

                # Charlie submits his order.
                await charlie.should_fuzzed_order(
                    symbol,
                    "main",
                    amount_range,
                    price_range,
                )


# Issue #3670: https://gitlab.com/dexlabs/derivadex/-/issues/3670
@pytest.mark.asyncio
async def test_match_market_order_breaches_max_taker_price_deviation(
    symbol, underlying
):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("1_000"), Decimal("1_000"))},
            ),
            client,
        ):
            # Alice deposits 10_000 USDC
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("10_000"))

            # Bob deposits 10_000 USDC
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("10_000"))

            # Alice submits her first order (post).
            await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("1"),
                Decimal("237"),
                Decimal("0"),
            )

            # Bob submit his first order (match - take no orders with no trade outcomes)
            await bob.should_take_no_orders(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Market,
                Decimal("1"),
                Decimal("0"),
                Decimal("0"),
                with_trade_outcomes=False,
            )


# Issue #3687: https://gitlab.com/dexlabs/derivadex/-/issues/3687
@pytest.mark.asyncio
async def test_issue_3687(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("1_100"), Decimal("1_600"))},
            ),
            client,
        ) as tick_generator:
            # Alice deposits 1_000 USDC
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("1_000"))

            # Bob deposits 1_000 USDC
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("1_000"))

            # Alice submits her first order (post). Her open margin fraction (omf) at this point is 1_000 / (1 * 1_100) = 0.9090. Since omf >= imf = 1 / 3, this order is sequenced.
            await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("1"),
                Decimal("1_100"),
                Decimal("0"),
            )

            # Bob submit his first order (match - complete fill). His omf at this point is 1_000 / (1 * 1_100) = 0.9090. Since omf >= imf = 1 / 3, this order is sequenced.
            # Alice successfully opens a short position of 1 <symbol> for an entry price of 1_000 USDC. Bob successfully opens a long position of 1 <symbol> for an entry price of 1_000 USDC.
            # They both have an unrealized pnl of 0.
            # Bob's order incurs a taker fee, and so his collateral reduces to 1_000 - 0.002 * 1.0 * 1_100 = 997.8.
            await bob.should_complete_fill_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("1"),
                Decimal("1_100"),
                Decimal("0"),
            )

            # Alice submits her second order (post). Her open margin fraction (omf) at this point is (1_000 + 250) / (2 * 1_100) = 0.5681. Since omf >= imf = 1 / 3, this order is sequenced.
            await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("1"),
                Decimal("1_600"),
                Decimal("0"),
            )

            # Bob submit his second order (post). His omf at this point is (997.8 + 501) / (2 * 1_100) = 0.6813. Since omf >= imf = 1 / 3, this order is sequenced.
            await bob.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("1"),
                Decimal("1_601"),
                Decimal("0"),
            )

            # Now, the index price moves to 1_600. The mark price here is 1_600.
            # Alice's mf is (1_000 - 500) / (1 * 1_600) = 0.3125, which is insolvent!
            # Bob's mf is (997.8 + 500) / (1 * 1_600) = 0.9361. He's okay.
            current = await default_match_all_up_to(
                store.advance_until_price(
                    tick_generator,
                    symbol,
                    PositionSide.Long,
                    Decimal("1_600"),
                )
            )
            current.default_match_rest()

            # Bob submits his second order (match - take no orders but with maker cancels).
            # His order matches Alice first. If Alice were to get the 1 filled by Bob, her mf would be (1000 - 250) / (2 * 1_600) = 0.2344 < 1 / 3.
            # Thus, the order gets clamped to a lower quantity in solvency guards so as to keep her mf above the imf, and the remainder of the maker order is canceled on the book.
            # Bob's order, after taking 0 of Alice's order, hits his own order, a self-match, and so the rest of his order is canceled and his market order is "completely" filled, not taking any orders, but having Alice's maker order canceled anyways as a result of Bob's request.
            await bob.should_take_no_orders(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Market,
                Decimal("1"),
                Decimal("0"),
                Decimal("0"),
                with_trade_outcomes=True,
            )


@pytest.mark.asyncio
async def test_post_only_order():
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {ETHP: "ETH/USD"},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-04-18"),
                duration="1m",
                price_ranges={ETHP: (Decimal("1_000"), Decimal("1_000"))},
            ),
            client,
        ):
            # Alice deposits 10_000 USDC into the main strategy
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("10_000"))

            # Bob deposits 10_000 USDC
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("10_000"))

            # Alice submits her first order (post).
            # Alice's order is a post-only order. There are no other orders on the book, so her order is posted.
            await alice.should_post_order(
                ETHP,
                "main",
                OrderSide.Ask,
                OrderType.PostOnlyLimit,
                Decimal("1"),
                Decimal("237"),
                Decimal("0"),
            )

            # Bob submits his first order (take no orders - post only violation).
            # Bob's order is a post-only order, and so although it would have matched with Alice's order if it were not a post-only order, it rejects the order as invalid and does not post it to the book.
            await bob.should_take_no_orders(
                ETHP,
                "main",
                OrderSide.Bid,
                OrderType.PostOnlyLimit,
                Decimal("1"),
                Decimal("237"),
                Decimal("0"),
                with_trade_outcomes=False,
            )


@pytest.mark.asyncio
async def test_cancel_all(symbol, underlying, symbol_2, underlying_2):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying, symbol_2: underlying_2},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={
                    symbol: (Decimal("236.5"), Decimal("236.5")),
                    symbol_2: (Decimal("300"), Decimal("300")),
                },
            ),
            client,
        ):
            # Alice deposits 10_000 USDC
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("10_000"))

            # Bob deposits 10_000 USDC
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("10_000"))

            # Alice submits her first order (post).
            await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("1"),
                Decimal("237"),
                Decimal("0"),
            )

            # Alice submits her second order (post).
            await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("1"),
                Decimal("238"),
                Decimal("0"),
            )

            # Alice submits her third order (post).
            await alice.should_post_order(
                symbol_2,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("1"),
                Decimal("301"),
                Decimal("0"),
            )

            # Bob submits his first order (post).
            await bob.should_post_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("1"),
                Decimal("236"),
                Decimal("0"),
            )

            # Bob submits her second order (post).
            await bob.should_post_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("1"),
                Decimal("235"),
                Decimal("0"),
            )

            # Bob submits her third order (post).
            await bob.should_post_order(
                symbol_2,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("1"),
                Decimal("299"),
                Decimal("0"),
            )

            # Alice cancels all her symbol orders.
            await alice.should_cancel_all(symbol, "main")


@pytest.mark.asyncio
async def test_prevent_self_match(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("1_000"), Decimal("1_000"))},
            ),
            client,
        ):
            # Alice deposits 10_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("10_000"))

            # Bob deposits 10_000 USDC.
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("10_000"))

            # Bob submits his order (post).
            await bob.should_post_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("1"),
                Decimal("3_400"),
                Decimal("0"),
            )

            # Alice submits her first order (post).
            await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("1"),
                Decimal("3_400"),
                Decimal("0"),
            )

            # Alice submits her second order (match - self-match).
            # Her order matches Bob first, who gets completely filled for a quantity of 1.
            # But Alice still has an ask of quantity 1 remaining, which matches with herself and is a self-match,
            # which cancels the remainder of the order and thus the result is a complete fill of quantity 1.
            await alice.should_complete_fill_order_cancel_remainder(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("2"),
                Decimal("3_400"),
                Decimal("0"),
            )


@pytest.mark.asyncio
async def test_prevent_self_match_no_fill(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("1_000"), Decimal("1_000"))},
            ),
            client,
            "prevent_self_match_no_fill",
        ):
            # Alice deposits 10_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("10_000"))

            # Alice submits her first order (post).
            await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("1"),
                Decimal("3_400"),
                Decimal("0"),
            )

            # Alice submits her second order (self-match), no state-transitioning actions should be taken.
            await alice.should_take_no_orders(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("2"),
                Decimal("3_400"),
                Decimal("0"),
                with_trade_outcomes=False,
            )


@pytest.mark.asyncio
async def test_prevent_limit_taker_order_below_imf(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("5_000"), Decimal("5_000"))},
            ),
            client,
        ):
            # For all the following interactions, the mark price is 5_000 as is the index price.

            # Alice deposits 5_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("5_000"))

            # Bob deposits 10_000 USDC.
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("10_000"))

            # Charlie deposits 5_000 USDC.
            charlie = AccountMatcher(Account(store.wallet.account_for_index(2)))
            await charlie.should_deposit("main", Decimal("5_000"))

            # Alice submits her order (post). Her open margin fraction (omf) at this point is 5_000 / (2 * 5_000) = 0.5. Since omf >= imf = 1 / 3, this order is sequenced.
            # Her margin fraction (mf) at this point is infinite.
            await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("2"),
                Decimal("5_000"),
                Decimal("0"),
            )

            # Bob submits his order (post). His omf at this point is 10_000 / (2 * 5_000) = 1. His mf at this point is infinite.
            await bob.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("2"),
                Decimal("5_100"),
                Decimal("0"),
            )

            # Charlie submits his order (match - solvency guard taker). His omf at this point is 5_000 / (3 * 5_000) = 1 / 3.
            # His order matches Alice first, who gets completely filled for a quantity of 2 @ 5_000.
            # His mf at this point is (5_000 - 20) / (2 * 5_000) = 0.4980 (0.002 * 5000 * 2 = 20 is taker fee).
            # Alice's mf at this point is 5_000 / (2 * 5_000) = 0.5.
            # But Charlie still has a bid of quantity 1 remaining. If he were to get the 1 filled by Bob's 1, his mf would be (4_980 - 10.2 - 100) / (3 * 5_000) = 0.3246 < 1 / 3 = imf (0.002 * 5_100 * 1 = 10.2 is taker fee, 100 is unrealized pnl),
            # and so the order gets clamped to a lower quantity in solvency guards so as to keep his mf above the imf, and "completely" fills at this lower quantity.
            await charlie.should_complete_fill_order_cancel_remainder(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("3"),
                Decimal("5_100"),
                Decimal("0"),
            )
            # The resulting transaction should be:
            # CompleteFill:
            #   - Alice: 2 @ 5_000
            #   - Bob: 0.9267 @ 5_100
            # (Charlie's remaining 0.0733 in his order intent is canceled.)
            # (Bob's 1.0733 @ 5_100 remains in the book.)


@pytest.mark.asyncio
async def test_prevent_limit_maker_order_below_imf(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("5_000"), Decimal("5_000"))},
            ),
            client,
        ):
            # For all the following interactions, the mark price is 5_000 as is the index price.

            # Alice deposits 5_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("5_000"))

            # Bob deposits 10_000 USDC.
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("10_000"))

            # Charlie deposits 5_000 USDC.
            charlie = AccountMatcher(Account(store.wallet.account_for_index(2)))
            await charlie.should_deposit("main", Decimal("5_000"))

            # Alice submits her order (post). Her open margin fraction (omf) at this point is 5_000 / (1.5 * 5_000) = 2 / 3. Since omf >= imf = 1 / 3, her order is sequenced.
            # Her mf at this point is infinite.
            await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("1.5"),
                Decimal("4_901"),
                Decimal("0"),
            )

            # Alice submits his second order (post). Her omf at this point is 5_000 / (3 * 5_000) = 1 / 3. Her mf at this point is infinite.
            await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("1.5"),
                Decimal("4_900"),
                Decimal("0"),
            )

            # Bob submits his market order (match - complete fill). His omf at this point is 10_000 / (1.5 * 5000) = 4 / 3.
            # His order matches Alice's second order, which gets completely filled for a quantity of 1.5 @ 4_900.
            # His mf at this point is (10_000 - 14.7 + 150) / (1.5 * 5_000) = 1.3514 (0.002 * 4900 * 1.5 = 14.7030 is taker fee, 150 is unrealized pnl).
            # Alice's mf at this point is (5_000 - 150) / (1.5 * 5_000) = 0.6467 (-150 is unrealized pnl).
            await bob.should_complete_fill_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Market,
                Decimal("1.5"),
                Decimal("0"),
                Decimal("0"),
            )

            # Charlie submits his order (match - solvency guard maker). His omf at this point is 5_000 / (1.5 * 5000) = 2 / 3.
            # His order matches Alice's first order, a quantity of 1.5 @ 4_901.
            # If Alice completely fills Charlie's order, Alice's mf would be (5_000 - 298.5) / (3 * 5_000) = 0.3134 < 1 / 3 = imf (-298.5 is unrealized pnl),
            # and so the order gets clamped to a lower quantity in solvency guards so as to keep her mf above the imf, and partially fills at this lower quantity.
            # The remainder of Alice's maker order already on the book is canceled.
            # This appears as a partial fill to the book since it is a limit order and so the remainder of Charlie's order is posted to the book.
            await charlie.should_partial_fill_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("1.5"),
                Decimal("4_995"),
                Decimal("0"),
            )
            # The resulting transaction should be:
            # PartialFill (post bid 0.1691 @ 4_995):
            #   - Alice: 1.3309 @ 4_901
            # (Alice's remaining 0.1691 @ 4_901 is canceled in the book.)


@pytest.mark.asyncio
async def test_prevent_market_taker_order_below_imf(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("5_000"), Decimal("5_000"))},
            ),
            client,
        ):
            # For all the following interactions, the mark price is 5_000 as is the index price.

            # Alice deposits 5_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("5_000"))

            # Bob deposits 10_000 USDC.
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("10_000"))

            # Charlie deposits 5_000 USDC.
            charlie = AccountMatcher(Account(store.wallet.account_for_index(2)))
            await charlie.should_deposit("main", Decimal("5_000"))

            # Alice submits her order (post). Her open margin fraction (omf) at this point is 5_000 / (2 * 5_000) = 0.5. Since omf >= imf = 1 / 3, this order is sequenced.
            # Her margin fraction (mf) at this point is infinite.
            await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("2"),
                Decimal("5_000"),
                Decimal("0"),
            )

            # Bob submits his order (post). His omf at this point is 10_000 / (2 * 5_000) = 1. His mf at this point is infinite.
            await bob.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("2"),
                Decimal("5_100"),
                Decimal("0"),
            )

            # Charlie submits his order (match - solvency guard taker). His omf at this point is 5_000 / (3 * 5_000) = 1 / 3.
            # His order matches Alice first, who gets completely filled for a quantity of 2 @ 5_000.
            # His mf at this point is (5_000 - 20) / (2 * 5_000) = 0.4980 (0.002 * 5000 * 2 = 20 is taker fee).
            # Alice's mf at this point is 5_000 / (2 * 5_000) = 0.5.
            # But Charlie still has a bid of quantity 1 remaining. If he were to get the 1 filled by Bob's 1, his mf would be (4_980 - 10.2 - 100) / (3 * 5_000) = 0.3246 < 1 / 3 = imf (0.002 * 5_100 * 1 = 10.2 is taker fee, 100 is unrealized pnl),
            # and so the order gets clamped to a lower quantity in solvency guards so as to keep his mf above the imf, and "completely" fills at this lower quantity.
            await charlie.should_complete_fill_order_cancel_remainder(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Market,
                Decimal("3"),
                Decimal("0"),
                Decimal("0"),
            )
            # The resulting transaction should be:
            # CompleteFill:
            #   - Alice: 2 @ 5_000
            #   - Bob: 0.9267 @ 5_100
            # (Charlie's remaining 0.0733 in his order intent is canceled.)
            # (Bob's 1.0733 @ 5_100 remains in the book.)


@pytest.mark.asyncio
async def test_prevent_market_maker_order_below_imf(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("5_000"), Decimal("5_000"))},
            ),
            client,
        ):
            # For all the following interactions, the mark price is 5_000 as is the index price.

            # Alice deposits 5_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("5_000"))

            # Bob deposits 10_000 USDC.
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("10_000"))

            # Charlie deposits 5_000 USDC.
            charlie = AccountMatcher(Account(store.wallet.account_for_index(2)))
            await charlie.should_deposit("main", Decimal("5_000"))

            # Alice submits her order (post). Her open margin fraction (omf) at this point is 5_000 / (1.5 * 5_000) = 2 / 3. Since omf >= imf = 1 / 3, her order is sequenced.
            # Her mf at this point is infinite.
            await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("1.5"),
                Decimal("4_901"),
                Decimal("0"),
            )

            # Alice submits his second order (post). Her omf at this point is 5_000 / (3 * 5_000) = 1 / 3. Her mf at this point is infinite.
            await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("1.5"),
                Decimal("4_900"),
                Decimal("0"),
            )

            # Bob submits his market order (match - complete fill). His omf at this point is 10_000 / (1.5 * 5000) = 4 / 3.
            # His order matches Alice's second order, which gets completely filled for a quantity of 1.5 @ 4_900.
            # His mf at this point is (10_000 - 14.7 + 150) / (1.5 * 5_000) = 1.3514 (0.002 * 4900 * 1.5 = 14.7030 is taker fee, 150 is unrealized pnl).
            # Alice's mf at this point is (5_000 - 150) / (1.5 * 5_000) = 0.6467 (-150 is unrealized pnl).
            await bob.should_complete_fill_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Market,
                Decimal("1.5"),
                Decimal("0"),
                Decimal("0"),
            )

            # Charlie submits his order (match - solvency guard maker). His omf at this point is 5_000 / (1.5 * 5000) = 2 / 3.
            # His order matches Alice's first order, a quantity of 1.5 @ 4_901.
            # If Alice completely fills Charlie's order, Alice's mf would be (5_000 - 298.5) / (3 * 5_000) = 0.3134 < 1 / 3 = imf (-298.5 is unrealized pnl),
            # and so the order gets clamped to a lower quantity in solvency guards so as to keep her mf above the imf, and partially fills at this lower quantity.
            # There is a remainder of Charlie's order that Alice cannot fill, or she would become insolvent. Thus, as taker, the remaining amount is posted to the book on behalf of Charlie.
            # The remainder of Alice's maker order already on the book is canceled.
            # This appears as a complete fill to the book since it is a market order.
            await charlie.should_complete_fill_order_cancel_remainder(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Market,
                Decimal("1.55"),
                Decimal("0"),
                Decimal("0"),
            )
            # The resulting transaction should be:
            # CompleteFill:
            #   - Alice: 1.3309 @ 4_901
            # (Charlie's remaining 0.2191 in his order intent is canceled.)
            # (Alice's remaining 0.1691 @ 4_901 is canceled in the book.)


@pytest.mark.asyncio
async def test_partial_fill_with_low_mf_no_solvency_guard(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("5_000"), Decimal("5_000"))},
            ),
            client,
        ):
            # For all the following interactions, the mark price is 5_000 as is the index price.

            # Alice deposits 5_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("5_000"))

            # Bob deposits 5_000 USDC.
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("5_000"))

            # Alice submits her order (post). Her open margin fraction (omf) at this point is 5_000 / (2 * 5_000) = 1 / 2. Since omf >= imf = 1 / 3, her order is sequenced.
            # Her mf at this point is infinite.
            await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("2.0"),
                Decimal("5_000"),
                Decimal("0"),
            )

            # Bob submits his order (post). His omf at this point is 5_000 / (3 * 5_100) = 0.3268 < 1 / 3 = imf. Bob's order would not pass validation and hence would not be sequenced.
            # For sake of argument assume that it is sequenced, assuming that Bob got to this point via price moves.
            # His order matches Alice, who gets completely filled for a quantity of 2 @ 5_000.
            # His mf at this point is (5_000 - 20) / (2 * 5_000) = 0.4980 (0.002 * 5000 * 2 = 20 is taker fee).
            # Alice's mf at this point is 5_000 / (2 * 5_000) = 0.5.
            # But Bob still has a bid of quantity 1 remaining. At this point, there are no remaining orders on the book to fill Bob's 1.
            # Thus, this is a partial fill, and the remaining 1 must be posted to the book.
            # However, if his 1 ever got filled at 5_000 (assuming mark price remains constant), he would have an mf of 4_980 / (3 * 5_000) = 0.3320 < 1 / 3 = imf. If this occurs later, he will get filled to the clamped amount, and the remaining amount will be canceled. This maker order canceled is covered in test_prevent_limit_maker_order_below_imf
            await bob.should_partial_fill_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("3.0"),
                Decimal("5_100"),
                Decimal("0"),
            )
            # The resulting transaction should be:
            # PartialFill (post bid 1 @ 5_100):
            #   - Alice: 2 @ 5_000


@pytest.mark.asyncio
async def test_market_taker_order_partial_fill_solvency_guard(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("5_000"), Decimal("5_000"))},
            ),
            client,
        ):
            # For all the following interactions, the mark price is 5_000 as is the index price.

            # Alice deposits 5_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("5_000"))

            # Bob deposits 5_000 USDC.
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("5_000"))

            # Alice submits her order (post). Her open margin fraction (omf) at this point is 5_000 / (2 * 5_000) = 1 / 2. Since omf >= imf = 1 / 3, her order is sequenced.
            # Her mf at this point is infinite.
            await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("2.0"),
                Decimal("5_000"),
                Decimal("0"),
            )

            # Bob submits his order (post). His omf at this point is 5_000 / (3 * 5_100) = 0.3268 < 1 / 3 = imf. Bob's order would not pass validation and hence would not be sequenced.
            # For sake of argument assume that it is sequenced, assuming that Bob got to this point via price moves.
            # His order matches Alice, who gets completely filled for a quantity of 2 @ 5_000.
            # His mf at this point is (5_000 - 20) / (2 * 5_000) = 0.4980 (0.002 * 5000 * 2 = 20 is taker fee).
            # Alice's mf at this point is 5_000 / (2 * 5_000) = 0.5.
            # But Bob still has a bid of quantity 1 remaining. At this point, there are no remaining orders on the book to fill Bob's 1.
            # Since this is a market order, this is a complete fill, and the remaining 1 gets dropped.
            await bob.should_complete_fill_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Market,
                Decimal("3.0"),
                Decimal("0"),
                Decimal("0"),
            )


all_tests = [
    test_post_entire_order,
    test_post_order_then_modify,
    test_modify_nonexistent_order,
    test_post_order_then_cancel,
    test_cancel_nonexistent_order,
    test_match_multiple_orders,
    test_fuzzed_match_multiple_orders,
    test_match_market_order_breaches_max_taker_price_deviation,
    test_issue_3687,
    test_cancel_all,
    test_prevent_self_match,
    test_prevent_self_match_no_fill,
    test_prevent_limit_taker_order_below_imf,
    test_prevent_limit_maker_order_below_imf,
    test_prevent_market_taker_order_below_imf,
    test_prevent_market_maker_order_below_imf,
    test_partial_fill_with_low_mf_no_solvency_guard,
    test_market_taker_order_partial_fill_solvency_guard,
]
