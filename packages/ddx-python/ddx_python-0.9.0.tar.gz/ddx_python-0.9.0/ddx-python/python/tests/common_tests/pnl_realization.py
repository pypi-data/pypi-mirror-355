import aiohttp
import pandas as pd
import pytest
from ddx._rust.common.enums import OrderSide, OrderType
from ddx._rust.decimal import Decimal
from tests.harness.account import Account
from tests.harness.market_data_driver.custom_market_data_driver import \
    CustomMarketDataDriver
from tests.harness.matchers.account import AccountMatcher
from tests.harness.matchers.tick import default_match_all_up_to
from tests.harness.store import Store


@pytest.mark.asyncio
async def test_pnl_realization_with_pnl(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="2m",
                price_ranges={symbol: (Decimal("2_000"), Decimal("2_000.5"))},
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
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("1.0"),
                Decimal("2_000"),
                Decimal("0"),
            )

            # Bob submits his first order (match - complete fill).
            # Alice successfully opens a long position of 1 <symbol> for an entry price of 2_000 USDC. Bob successfully opens a short position of 1 <symbol> for an entry price of 2_000 USDC.
            # They both have an unrealized pnl of 0.
            # Bob's order incurs a taker fee, and so his collateral reduces to 10_000 - 0.002 * 1.0 * 2_000 = 9_996.
            await bob.should_complete_fill_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("1.0"),
                Decimal("2_000"),
                Decimal("0"),
            )

            # Bob submits his second order (post). This is the ensure the mark price is initialized to 2_000. Note however, that the funding rate will be 0.
            await bob.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("0.1"),
                Decimal("2_000"),
                Decimal("0"),
            )

            # Now, the index price moves to 2_000.05. The mark price here is 2_000.452654.
            # Unrealized pnl becomes realized here. Alice now has a realized pnl of +0.452654. Bob has a realized pnl of -0.452654. Alice now has a avaiable collateral balance of 10_000.452654. Bob has a avaiable collateral balance of 9_995.547346.
            # There is not a substantial enough difference between the index price and the mark price, resulting in a zero funding rate.
            current = await default_match_all_up_to(
                store.advance_until_next_pnl_realization_period(tick_generator)
            )

            current.should_advance_settlement_epoch_with_pnl_realization()
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. realized pnl and funding payment updates to strategies).


all_tests = [
    test_pnl_realization_with_pnl,
]
