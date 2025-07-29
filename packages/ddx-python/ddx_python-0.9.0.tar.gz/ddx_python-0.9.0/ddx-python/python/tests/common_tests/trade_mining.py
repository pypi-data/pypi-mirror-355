import os

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
async def test_trade_mining_with_volume(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={
                    symbol: (Decimal("100"), Decimal("100")),
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

            # Alice submits her first order (post).
            await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("0.1"),
                Decimal("100"),
                Decimal("0"),
            )

            # Advance two ticks so that trade volume is recorded
            await anext(tick_generator)
            await anext(tick_generator)

            # Bob submits his first order (match - complete fill).
            # Alice successfully opens a short position of 0.1 <symbol> for an entry price of 100 USDC. Bob successfully opens a long position of 0.1 <symbol> for an entry price of 100 USDC.
            await bob.should_complete_fill_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("0.1"),
                Decimal("100"),
                Decimal("0"),
            )

            current = await default_match_all_up_to(
                store.advance_until_next_trade_mining_period(
                    tick_generator,
                )
            )

            current.should_advance_settlement_epoch_with_trade_mining()
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. ddx distribution from trade mining).


@pytest.mark.asyncio
async def test_trade_mining_unrecorded_volume(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={
                    symbol: (Decimal("100"), Decimal("100")),
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

            # Alice submits her first order (post).
            await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("0.1"),
                Decimal("100"),
                Decimal("0"),
            )

            # Do not advance any ticks so that trade volume remains unrecorded

            # Bob submits his first order (match - complete fill).
            # Alice successfully opens a short position of 0.1 <symbol> for an entry price of 100 USDC. Bob successfully opens a long position of 0.1 <symbol> for an entry price of 100 USDC.
            await bob.should_complete_fill_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("0.1"),
                Decimal("100"),
                Decimal("0"),
            )

            current = await default_match_all_up_to(
                store.advance_until_next_trade_mining_period(
                    tick_generator,
                )
            )

            current.should_advance_settlement_epoch_with_trade_mining(negative=True)
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. no ddx distribution from trade mining).


@pytest.mark.asyncio
async def test_trade_mining_no_volume(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={
                    symbol: (Decimal("100"), Decimal("100")),
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

            current = await default_match_all_up_to(
                store.advance_until_next_trade_mining_period(
                    tick_generator,
                )
            )

            current.should_advance_settlement_epoch_with_trade_mining(negative=True)
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. no ddx distribution from trade mining).


@pytest.mark.asyncio
async def test_trade_mining_with_volume_after_end(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="4m",
                price_ranges={
                    symbol: (Decimal("100"), Decimal("100")),
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

            for _ in range(store.trade_mining_params.trade_mining_length):
                current = await default_match_all_up_to(
                    store.advance_until_next_trade_mining_period(
                        tick_generator,
                    )
                )

                current.should_advance_settlement_epoch()
                current.default_match_rest()

            # Alice submits her first order (post).
            await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("0.1"),
                Decimal("100"),
                Decimal("0"),
            )

            # Advance two ticks so that trade volume would have been recorded
            await anext(tick_generator)
            await anext(tick_generator)

            # Bob submits his first order (match - complete fill).
            # Alice successfully opens a short position of 0.1 <symbol> for an entry price of 100 USDC. Bob successfully opens a long position of 0.1 <symbol> for an entry price of 100 USDC.
            await bob.should_complete_fill_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("0.1"),
                Decimal("100"),
                Decimal("0"),
            )

            current = await default_match_all_up_to(
                store.advance_until_next_trade_mining_period(
                    tick_generator,
                )
            )

            current.should_advance_settlement_epoch_with_trade_mining(negative=True)
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. ddx distribution from trade mining).


all_tests = [
    test_trade_mining_with_volume,
    test_trade_mining_unrecorded_volume,
    test_trade_mining_no_volume,
    test_trade_mining_with_volume_after_end,
]
