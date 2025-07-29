import logging
import random

import aiohttp
import pandas as pd
import pytest
from ddx._rust.common.enums import OrderSide, OrderType
from ddx._rust.decimal import Decimal
from tests.harness.account import Account
from tests.harness.market_data_driver.custom_market_data_driver import \
    CustomMarketDataDriver
from tests.harness.matchers.account import AccountMatcher
from tests.harness.matchers.fuzzed_account import FuzzedAccountMatcher
from tests.harness.matchers.tick import default_match_all_up_to
from tests.harness.store import Store

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_liquidation_no_adl(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("100"), Decimal("145"))},
            ),
            client,
            version_db=[
                "PartialFill",
                "CompleteFill",
                "Post",
                "Liquidation",
                "StrategyUpdate",
                "Funding",
                "TradeMining",
            ],
        ) as tick_generator:
            # Alice deposits 5_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("5_000"))

            # Bob deposits 10_000 USDC.
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("10_000"))

            # Alice submits her first order (post).
            _, (order_nonce, _) = await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("100"),
                Decimal("100"),
                Decimal("0"),
            )

            # Bob submits his first order (match - complete fill).
            # Alice successfully opens a short position of 100 <symbol> for an entry price of 100 USDC. Bob successfully opens a long position of 100 <symbol> for an entry price of 100 USDC.
            # Bob incurs a taker fee, and so his collateral reduces to 10_000 - 0.002 * 100 * 100 = 9_980.
            # Alice's margin fraction (mf) at this point is 5_000 / (100 * 100) = 0.5. Bob's mf at this point is 9_980 / (100 * 100) = 0.998.
            await bob.should_complete_fill_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("100"),
                Decimal("100"),
                Decimal("0"),
            )

            # Bob submits his second order (post). This is to ensure no ADL occurs.
            await bob.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("100"),
                Decimal("145"),
                Decimal("0"),
            )

            # Now, the index price moves to 145. The mark price here is 145. (Note that the precise liquidation price is 142.8571, however for the sake of round numbers the we send the price update of 145.)
            # Alice's mf at this point is (5_000 - 4_500) / (100 * 145) = 0.03448 (uh-oh!) where -4_500 is her unrealized pnl.
            # Bob's mf at this point is (9_980 + 4_500) / (100 * 145) = 0.9986 where +4_500 is his unrealized pnl.
            # Alice's mf is lower than the maintenance margin fraction (mmf) of 0.05! Alice will get liquidated.
            # Alice's bankruptcy price is 145 + (5_000 - 4_500) / 100 = 150. This mark price is the point at which Alice's total value of her positions is 0 (her unrealized pnl at this point would be -5_000, so her total value at this point would be 5_000 - 5_000 = 0).
            # Alice's position is sold to the open market as a market order bid. Her taker, Bob, gets filled at the full amount of 100 @ 145.
            # The exchange is lucky here, as there is a positive price delta from this trade, 150 - 145 = 5, meaning that after filling the trade 100 @ 145, there will still be USDC left in the account that will go to the insurance fund. Namely, 5_000 - 4_500 = 500 will go to the organic insurance fund.
            # The main criteria that was checked here was `insurance_fund_cap + liquidation_spread >= 0`, where `liquidation_spread = price_delta * fill_amount`. Here, liquidation_spread was positive since price_delta was positive, meaning that the exchange profited from the liquidation sale. Thus, insurance funds were not needed and were instead added to. However, if the liquidation_spread were negative (due to the price_delta being negative), funds from the organic insurance fund would be needed to cover losses on an immediate liquidation sale, subject to the above nonnegativity constraint. To satisfy this constraint it is sufficient to clamp the possible_fill_amount with a max fill amount of `insurance_fund_cap / |price_delta|` or less. For more details, see `derivadex/rust-packages/ddx-operator/enclave/src/execution/liquidation.rs`.
            # Finally, note that the fill amount undergoes a final check, Bob's solvency guard, and Bob successfully closes his previous long position of 100 <symbol> for an exit price of 145 USDC because after the full trade, his mf becomes infinite once more as he has zero outstanding notional.
            # Alice's collateral at this point is 5_000 - 5_000 = 0. She has been fully liquidated. Bob's collateral at this point is 9_980 + 4_500 = 14_480. (Note: takers of the liquidated position do not incur any taker fees.)
            current = await default_match_all_up_to(
                store.advance_until_liquidation_price(
                    tick_generator,
                    alice.position_ids[order_nonce],
                )
            )

            current.should_process_price_with_liquidations()
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. liquidations due to a new index price).


@pytest.mark.asyncio
async def test_liquidation_no_adl_negative_margin_fraction(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("100"), Decimal("155"))},
            ),
            client,
        ) as tick_generator:
            # Alice deposits 5_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("5_000"))

            # Bob deposits 10_000 USDC.
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("10_000"))

            # Alice submits her first order (post).
            _, (order_nonce, _) = await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("100"),
                Decimal("100"),
                Decimal("0"),
            )

            # Bob submits his first order (match - complete fill).
            # Alice successfully opens a short position of 100 <symbol> for an entry price of 100 USDC. Bob successfully opens a long position of 100 <symbol> for an entry price of 100 USDC.
            # Bob incurs a taker fee, and so his collateral reduces to 10_000 - 0.002 * 100 * 100 = 9_980.
            # Alice's margin fraction (mf) at this point is 5_000 / (100 * 100) = 0.5. Bob's mf at this point is 9_980 / (100 * 100) = 0.998.
            await bob.should_complete_fill_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("100"),
                Decimal("100"),
                Decimal("0"),
            )

            # Bob submits his second order (post). This is to ensure no ADL occurs.
            await bob.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("100"),
                Decimal("145"),
                Decimal("0"),
            )

            # Now, the index price moves to 155. The mark price here is 155. (Note that the precise liquidation price is 142.8571, however for the sake of round numbers and to force a negative margin fraction we send the price update of 155.)
            # Alice's mf at this point is (5_000 - 5_500) / (100 * 155) = -0.03225 (uh-oh!) where -5_500 is her unrealized pnl.
            # Bob's mf at this point is (9_980 + 5_500) / (100 * 155) = 0.99870 where +5_500 is his unrealized pnl.
            # Alice's mf is lower than the maintenance margin fraction (mmf) of 0.05! Alice will get liquidated.
            # Alice's bankruptcy price is 155 + (5_000 - 5_500) / 100 = 150. This mark price is the point at which Alice's total value of her positions is 0 (her unrealized pnl at this point would be -5_000, so her total value at this point would be 5_000 - 5_000 = 0).
            # (Technically, her total value is actually already negative because the mark price is actually past the bankruptcy price!)
            # Alice's position is sold to the open market as a market order bid. Her taker, Bob, gets filled at the full amount of 100 @ 145.
            # The exchange is lucky here, as there is a positive price delta from this trade, 150 - 145 = 5, meaning that after filling the trade 100 @ 145, there will still be USDC left in the account that will go to the insurance fund. Namely, 5_000 - 4_500 = 500 will go to the organic insurance fund.
            # The main criteria that was checked here was `insurance_fund_cap + liquidation_spread >= 0`, where `liquidation_spread = price_delta * fill_amount`. Here, liquidation_spread was positive since price_delta was positive, meaning that the exchange profited from the liquidation sale. Thus, insurance funds were not needed and were instead added to. However, if the liquidation_spread were negative (due to the price_delta being negative), funds from the organic insurance fund would be needed to cover losses on an immediate liquidation sale, subject to the above nonnegativity constraint. To satisfy this constraint it is sufficient to clamp the possible_fill_amount with a max fill amount of `insurance_fund_cap / |price_delta|` or less. For more details, see `derivadex/rust-packages/ddx-operator/enclave/src/execution/liquidation.rs`.
            # Finally, note that the fill amount undergoes a final check, Bob's solvency guard, and Bob successfully closes his previous long position of 100 <symbol> for an exit price of 145 USDC because after the full trade, his mf becomes infinite once more as he has zero outstanding notional.
            # Alice's collateral at this point is 5_000 - 5_000 = 0. She has been fully liquidated. Bob's collateral at this point is 9_980 + 4_500 = 14_480. (Note: takers of the liquidated position do not incur any taker fees.)
            current = await default_match_all_up_to(
                store.advance_until_liquidation_price(
                    tick_generator,
                    alice.position_ids[order_nonce],
                )
            )

            current.should_process_price_with_liquidations()
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. liquidations due to a new index price).


@pytest.mark.asyncio
async def test_mul_liquidations_vs_same_maker_order_no_adl(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("100"), Decimal("145"))},
            ),
            client,
        ) as tick_generator:
            # Alice deposits 5_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("5_000"))

            # Bob deposits 10_000 USDC.
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("10_000"))

            # Charlie deposits 5_000 USDC.
            charlie = AccountMatcher(Account(store.wallet.account_for_index(2)))
            await charlie.should_deposit("main", Decimal("5_000"))

            # Alice submits her first order (post).
            _, (order_nonce, _) = await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("100"),
                Decimal("100"),
                Decimal("0"),
            )

            # Charlie submits his first order (post).
            await charlie.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("100"),
                Decimal("100"),
                Decimal("0"),
            )

            # Bob submits his first order (match - complete fill).
            # Alice and Charlie each successfully open a short position of 100 <symbol> for an entry price of 100 USDC. Bob successfully opens a long position of 200 <symbol> for an entry price of 100 USDC.
            # Bob incurs a taker fee, and so his collateral reduces to 10_000 - 0.002 * 200 * 100 = 9_960.
            # Alice's margin fraction (mf) at this point is 5_000 / (100 * 100) = 0.5. Charlie's mf at this point is 5_000 / (100 * 100) = 0.5. Bob's mf at this point is 9_960 / (200 * 100) = 0.498.
            await bob.should_complete_fill_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("200"),
                Decimal("100"),
                Decimal("0"),
            )

            # Bob submits his second order (post). This is to ensure no ADL occurs.
            await bob.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("200"),
                Decimal("145"),
                Decimal("0"),
            )

            # Now, the index price moves to 145. The mark price here is 145. (Note that the precise liquidation price is 142.8571, however for the sake of round numbers the we send the price update of 145.)
            # Alice's mf at this point is (5_000 - 4_500) / (100 * 145) = 0.03448 (uh-oh!) where -4_500 is her unrealized pnl.
            # Charlie's mf at this point is (5_000 - 4_500) / (100 * 145) = 0.03448 (uh-oh!) where -4_500 is his unrealized pnl.
            # Bob's mf at this point is (9_960 + 9_000) / (200 * 145) = 0.6538 where +9_900 is his unrealized pnl.
            # Alice's and Charlie's mf are lower than the maintenance margin fraction (mmf) of 0.05! They will both get liquidated.
            # Both of their bankruptcy prices are 145 + (5_000 - 4_500) / 100 = 150. This mark price is the point at which the total value of each of their positions is 0 (the unrealized pnl at this point would be -5_000, so total value at this point would be 5_000 - 5_000 = 0).
            # Alice's position is sold first to the open market as a market order bid. Her taker, Bob, gets partially filled at the full amount of 100 @ 145.
            # The exchange is lucky here, as there is a positive price delta from this trade, 150 - 145 = 5, meaning that after filling the trade 100 @ 145, there will still be USDC left in the account that will go to the insurance fund. Namely, 5_000 - 4_500 = 500 will go to the organic insurance fund.
            # Similarly, Charlie's position is sold to the open market as a market order bid. His taker, Bob, gets completely filled at the full amount of 100 @ 145.
            # Another 500 will go to the organic insurance fund.
            # The main criteria that was checked here was `insurance_fund_cap + liquidation_spread >= 0`, where `liquidation_spread = price_delta * fill_amount`. Here, liquidation_spread was positive since price_delta was positive, meaning that the exchange profited from the liquidation sale. Thus, insurance funds were not needed and were instead added to. However, if the liquidation_spread were negative (due to the price_delta being negative), funds from the organic insurance fund would be needed to cover losses on an immediate liquidation sale, subject to the above nonnegativity constraint. To satisfy this constraint it is sufficient to clamp the possible_fill_amount with a max fill amount of `insurance_fund_cap / |price_delta|` or less. For more details, see `derivadex/rust-packages/ddx-operator/enclave/src/execution/liquidation.rs`.
            # Finally, note that the fill amount undergoes two final checks, Bob's solvency guard (twice, once for making Alice's order of 100 @ 145 and once for making Charlie's order of 100 @ 145), and Bob successfully closes his previous long position of 200 <symbol> for an exit price of 145 USDC because after the full trade, his mf becomes infinite once more as he has zero outstanding notional.
            # Alice's collateral at this point is 5_000 - 5_000 = 0. Charlie's is also 0. They have been fully liquidated. Bob's collateral at this point is 9_960 + 9_000 = 18_960. (Note: takers of liquidated positions do not incur any taker fees.)
            current = await default_match_all_up_to(
                store.advance_until_liquidation_price(
                    tick_generator,
                    alice.position_ids[order_nonce],
                )
            )

            current.should_process_price_with_liquidations()
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. liquidations due to a new index price).


@pytest.mark.asyncio
async def test_liquidation_self_match_no_adl(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("100"), Decimal("145"))},
            ),
            client,
        ) as tick_generator:
            # Alice deposits 5_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("5_000"))

            # Bob deposits 10_000 USDC.
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("10_000"))

            # Alice submits her first order (post).
            _, (order_nonce, _) = await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("100"),
                Decimal("100"),
                Decimal("0"),
            )

            # Bob submits his first order (match - complete fill).
            # Alice successfully opens a short position of 100 <symbol> for an entry price of 100 USDC. Bob successfully opens a long position of 100 <symbol> for an entry price of 100 USDC.
            # Bob incurs a taker fee, and so his collateral reduces to 10_000 - 0.002 * 100 * 100 = 9_980.
            # Alice's margin fraction (mf) at this point is 5_000 / (100 * 100) = 0.5. Bob's mf at this point is 9_800 / (100 * 100) = 0.98.
            await bob.should_complete_fill_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("100"),
                Decimal("100"),
                Decimal("0"),
            )

            # Alice submits her second order (post). This is to set the stage for the "self match". We want to prevent against Alice's other soon-to-be liquidated positions to be included in the matching orders for her liquidation sale.
            await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("0.01"),
                Decimal("145"),
                Decimal("0"),
            )

            # Bob submits his second order (post). This is to ensure no ADL occurs.
            await bob.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("100"),
                Decimal("145"),
                Decimal("0"),
            )

            # Now, the index price moves to 145. The mark price here is 145. (Note that the precise liquidation price is 142.8571, however for the sake of round numbers the we send the price update of 145.)
            # Alice's mf at this point is (5_000 - 4_500) / (100 * 145) = 0.03448 (uh-oh!) where -4_500 is her unrealized pnl.
            # Bob's mf at this point is (9_980 + 4_500) / (100 * 145) = 0.9986 where +4_500 is her unrealized pnl.
            # Alice's mf is lower than the maintenance margin fraction (mmf) of 0.05! Alice will get liquidated.
            # Alice's bankruptcy price is 145 + (5_000 - 4_500) / 100 = 150. This mark price is the point at which Alice's total value of her positions is 0 (her unrealized pnl at this point would be -5_000, so her total value at this point would be 5_000 - 5_000 = 0).
            # Alice's position is sold to the open market as a market order bid.
            # Although Alice's other order, 0.01 @ 145, arrived first, it is not included in the matching orders for her liquidation sale because it belongs to a trader who is currently in the process of being liquidated. Alice's ask for 0.01 @ 145 will indeed be canceled at the end of the liquidation process as her entire strategy will have been liquidated, including all of her open orders.
            # Her taker, Bob, gets filled at the full amount of 100 @ 145.
            # The exchange is lucky here, as there is a positive price delta from this trade, 150 - 145 = 5, meaning that after filling the trade 100 @ 145, there will still be USDC left in the account that will go to the insurance fund. Namely, 5_000 - 4_500 = 500 will go to the organic insurance fund.
            # The main criteria that was checked here was `insurance_fund_cap + liquidation_spread >= 0`, where `liquidation_spread = price_delta * fill_amount`. Here, liquidation_spread was positive since price_delta was positive, meaning that the exchange profited from the liquidation sale. Thus, insurance funds were not needed and were instead added to. However, if the liquidation_spread were negative (due to the price_delta being negative), funds from the organic insurance fund would be needed to cover losses on an immediate liquidation sale, subject to the above nonnegativity constraint. To satisfy this constraint it is sufficient to clamp the possible_fill_amount with a max fill amount of `insurance_fund_cap / |price_delta|` or less. For more details, see `derivadex/rust-packages/ddx-operator/enclave/src/execution/liquidation.rs`.
            # Finally, note that the fill amount undergoes a final check, Bob's solvency guard, and Bob successfully closes his previous long position of 100 <symbol> for an exit price of 145 USDC because after the full trade, his mf becomes infinite once more as he has zero outstanding notional.
            # Alice's collateral at this point is 5_000 - 5_000 = 0. She has been fully liquidated. Bob's collateral at this point is 9_980 + 4500 = 14_480. (Note: takers of the liquidated position do not incur any taker fees.)
            current = await default_match_all_up_to(
                store.advance_until_liquidation_price(
                    tick_generator, alice.position_ids[order_nonce]
                )
            )

            current.should_process_price_with_liquidations()
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. liquidations due to a new index price).


@pytest.mark.asyncio
async def test_liquidation_no_adl_using_insurance_fund(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("100"), Decimal("150"))},
            ),
            client,
        ) as tick_generator:
            # Alice deposits 5_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("5_000"))

            # Bob deposits 10_000 USDC.
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("10_000"))

            # Alice submits her first order (post).
            _, (order_nonce, _) = await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("100"),
                Decimal("100"),
                Decimal("0"),
            )

            # Bob submits his first order (match - complete fill).
            # Alice successfully opens a short position of 100 <symbol> for an entry price of 100 USDC. Bob successfully opens a long position of 100 <symbol> for an entry price of 100 USDC.
            # Bob incurs a taker fee, and so his collateral reduces to 10_000 - 0.002 * 100 * 100 = 9_980.
            # Alice's margin fraction (mf) at this point is 5_000 / (100 * 100) = 0.5. Bob's mf at this point is 9_980 / (100 * 100) = 0.998.
            await bob.should_complete_fill_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("100"),
                Decimal("100"),
                Decimal("0"),
            )

            # Bob submits his second order (post). This is to ensure no ADL occurs.
            await bob.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("100"),
                Decimal("150.1"),
                Decimal("0"),
            )

            # Now, the index price moves to 150. The mark price here is 150.006451. (Note that the precise liquidation price is 142.8571, however we send the price update of 150 to simulate a flash rally.)
            # Alice's mf at this point is (5_000 - 5_000.6451) / (100 * 150.006451) = -0.000043 (uh-oh!) where -5_000.6451 is her unrealized pnl. Note that due to the suddenness of the price movement, her total value is actually negative.
            # Bob's mf at this point is (9_980 + 5_000.6451) / (100 * 150.006451) = 0.9987 where +5_000.6451 is her unrealized pnl.
            # Alice's mf is lower than the maintenance margin fraction (mmf) of 0.05! Alice will get liquidated.
            # Alice's bankruptcy price is 150.006451 + (5_000 - 5_000.6451) / 100 = 150. This mark price is the point at which Alice's total value of her positions is 0 (her unrealized pnl at this point would be -5_000, so her total value at this point would be 5_000 - 5_000 = 0).
            # Alice's position is sold to the open market as a market order bid. Her taker, Bob, gets filled at the full amount of 100 @ 150.1. This price is within the max taker price deviation of the mark price 150.006451, 153.0066. So this order is eligible for matching.
            # The exchange is unlucky but also lucky here, as although there is a negative price delta from this trade, 150 - 150.1 = -0.1, there will still be a positive insurance fund. After filling the trade 100 @ 150.1, the insurance fund will be left with 20 - 10 = 10.
            # The main criteria that was checked here was `insurance_fund_cap + liquidation_spread >= 0`, where `liquidation_spread = price_delta * fill_amount`. Here, liquidation_spread was positive since price_delta was positive, meaning that the exchange profited from the liquidation sale. Thus, insurance funds were not needed and were instead added to. However, if the liquidation_spread were negative (due to the price_delta being negative), funds from the organic insurance fund would be needed to cover losses on an immediate liquidation sale, subject to the above nonnegativity constraint. To satisfy this constraint it is sufficient to clamp the possible_fill_amount with a max fill amount of `insurance_fund_cap / |price_delta|` or less. For more details, see `derivadex/rust-packages/ddx-operator/enclave/src/execution/liquidation.rs`.
            # Finally, note that the fill amount undergoes a final check, Bob's solvency guard, and Bob successfully closes his previous long position of 100 <symbol> for an exit price of 150.1 USDC because after the full trade, his mf becomes infinite once more as he has zero outstanding notional.
            # Alice's collateral at this point is 5_000 - 5_000 = 0. She has been fully liquidated. Bob's collateral at this point is 9_980 + 5_010 = 14_990. (Note: takers of the liquidated position do not incur any taker fees.)
            current = await default_match_all_up_to(
                store.advance_until_liquidation_price(
                    tick_generator,
                    alice.position_ids[order_nonce],
                )
            )

            current.should_process_price_with_liquidations()
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. liquidations due to a new index price).


@pytest.mark.asyncio
async def test_liquidation_with_adl_strategy_collision(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("100"), Decimal("145"))},
            ),
            client,
        ) as tick_generator:
            # Alice deposits 5_000 USDC. Because the two strategies result in a collision, we use the first strategy. The rest of the scenario should proceed the same as the one without the strategy collision
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main-50315", Decimal("2_500"))
            await alice.should_deposit("main-88428", Decimal("2_500"))

            # Alice also deposits 5_000 USDC, just to show that strategies that don't have a hash collision are treated as separate accounts
            await alice.should_deposit("main", Decimal("5_000"))

            # Bob deposits 10_000 USDC.
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("10_000"))

            # Alice submits her first order (post).
            _, (order_nonce, _) = await alice.should_post_order(
                symbol,
                "main-50315",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("100"),
                Decimal("100"),
                Decimal("0"),
            )

            # Bob submits his first order (match - complete fill).
            # Alice successfully opens a short position of 100 <symbol> for an entry price of 100 USDC. Bob successfully opens a long position of 100 <symbol> for an entry price of 100 USDC.
            # Bob incurs a taker fee, and so his collateral reduces to 10_000 - 0.002 * 100 * 100 = 9_980.
            # Alice's margin fraction (mf) at this point is 5_000 / (100 * 100) = 0.5. Bob's mf at this point is 9_980 / (100 * 100) = 0.998
            await bob.should_complete_fill_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("100"),
                Decimal("100"),
                Decimal("0"),
            )

            # Now, the index price moves to 145. The mark price here is 145. (Note that the precise liquidation price is 142.8571, however for the sake of round numbers the we send the price update of 145.)
            # Alice's mf at this point is (5_000 - 4_500) / (100 * 145) = 0.03448 (uh-oh!) where -4_500 is her unrealized pnl.
            # Bob's mf at this point is (9_980 + 4_500) / (100 * 145) = 0.9986 where +4_500 is her unrealized pnl.
            # Alice's mf is lower than the maintenance margin fraction (mmf) of 0.05! Alice will get liquidated.
            # Alice's bankruptcy price is 145 + (5_000 - 4_500) / 100 = 150. This mark price is the point at which Alice's total value of her positions is 0 (her unrealized pnl at this point would be -5_000, so her total value at this point would be 5_000 - 5_000 = 0).
            # Alice's position is attempted to be sold to the open market as a market order bid. However, there are no orders in the book and there remains a full balance of 100 <symbol> on the liquidated position. Thus, the exchange starts ADL'ing other positions by highest unrealized pnl first, position key second. However, in this case, there is only one position, Bob's long of 100 <symbol>.
            # Bob's long position is automatically closed by the exchange at the bankruptcy price of 150. Alice's realized pnl from her liquidated position is -5_000, and her collateral after Bob's position is closed is 5_000 - 5_000 = 0. Bob's realized pnl from his closed position is 5_000, and his collateral after his position is closed is 9_980 + 5_000 = 14_980. (Note: ADL'd traders do not incur any taker fees for their ADL.)
            # Since Alice's collateral at this point is 0, she has been fully liquidated. Bob has also been ADL'd and his long position closed by the exchange.
            current = await default_match_all_up_to(
                store.advance_until_liquidation_price(
                    tick_generator,
                    alice.position_ids[order_nonce],
                )
            )

            current.should_process_price_with_liquidations()
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. liquidations due to a new index price).


@pytest.mark.asyncio
async def test_liquidation_with_adl(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("100"), Decimal("145"))},
            ),
            client,
        ) as tick_generator:
            # Alice deposits 5_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("5_000"))

            # Bob deposits 10_000 USDC.
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("10_000"))

            # Alice submits her first order (post).
            _, (order_nonce, _) = await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("100"),
                Decimal("100"),
                Decimal("0"),
            )

            # Bob submits his first order (match - complete fill).
            # Alice successfully opens a short position of 100 <symbol> for an entry price of 100 USDC. Bob successfully opens a long position of 100 <symbol> for an entry price of 100 USDC.
            # Bob incurs a taker fee, and so his collateral reduces to 10_000 - 0.002 * 100 * 100 = 9_980.
            # Alice's margin fraction (mf) at this point is 5_000 / (100 * 100) = 0.5. Bob's mf at this point is 9_980 / (100 * 100) = 0.998
            await bob.should_complete_fill_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("100"),
                Decimal("100"),
                Decimal("0"),
            )

            # Now, the index price moves to 145. The mark price here is 145. (Note that the precise liquidation price is 142.8571, however for the sake of round numbers the we send the price update of 145.)
            # Alice's mf at this point is (5_000 - 4_500) / (100 * 145) = 0.03448 (uh-oh!) where -4_500 is her unrealized pnl.
            # Bob's mf at this point is (9_980 + 4_500) / (100 * 145) = 0.9986 where +4_500 is her unrealized pnl.
            # Alice's mf is lower than the maintenance margin fraction (mmf) of 0.05! Alice will get liquidated.
            # Alice's bankruptcy price is 145 + (5_000 - 4_500) / 100 = 150. This mark price is the point at which Alice's total value of her positions is 0 (her unrealized pnl at this point would be -5_000, so her total value at this point would be 5_000 - 5_000 = 0).
            # Alice's position is attempted to be sold to the open market as a market order bid. However, there are no orders in the book and there remains a full balance of 100 <symbol> on the liquidated position. Thus, the exchange starts ADL'ing other positions by highest unrealized pnl first, position key second. However, in this case, there is only one position, Bob's long of 100 <symbol>.
            # Bob's long position is automatically closed by the exchange at the bankruptcy price of 150. Alice's realized pnl from her liquidated position is -5_000, and her collateral after Bob's position is closed is 5_000 - 5_000 = 0. Bob's realized pnl from his closed position is 5_000, and his collateral after his position is closed is 9_980 + 5_000 = 14_980. (Note: ADL'd traders do not incur any taker fees for their ADL.)
            # Since Alice's collateral at this point is 0, she has been fully liquidated. Bob has also been ADL'd and his long position closed by the exchange.
            current = await default_match_all_up_to(
                store.advance_until_liquidation_price(
                    tick_generator,
                    alice.position_ids[order_nonce],
                )
            )

            current.should_process_price_with_liquidations()
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. liquidations due to a new index price).


# Issue 3933: https://gitlab.com/dexlabs/derivadex/-/issues/3933
@pytest.mark.asyncio
async def test_liquidation_with_mul_adl(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("100"), Decimal("145"))},
            ),
            client,
        ) as tick_generator:
            # Alice deposits 5_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("5_000"))

            # Bob deposits 10_000 USDC.
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("10_000"))

            # Charlie deposits 10_000 USDC.
            charlie = AccountMatcher(Account(store.wallet.account_for_index(2)))
            await charlie.should_deposit("main", Decimal("10_000"))

            # Alice submits her first order (post).
            _, (order_nonce, _) = await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("100"),
                Decimal("100"),
                Decimal("0"),
            )

            # Bob submits his first order (match - complete fill).
            # Alice successfully opens a short position of 50 <symbol> for an entry price of 100 USDC. Bob successfully opens a long position of 50 <symbol> for an entry price of 100 USDC.
            # Bob incurs a taker fee, and so his collateral reduces to 10_000 - 0.002 * 100 * 50 = 9_990.
            # Alice's margin fraction (mf) at this point is 5_000 / (100 * 50) = 1. Bob's mf at this point is 9_980 / (100 * 50) = 1.996.
            await bob.should_complete_fill_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("50"),
                Decimal("100"),
                Decimal("0"),
            )

            # Charlie submits his first order (match - complete fill).
            # Alice successfully opens a short position of 50 <symbol> for an entry price of 100 USDC. Charlie successfully opens a long position of 50 <symbol> for an entry price of 100 USDC.
            # Charlie incurs a taker fee, and so his collateral reduces to 10_000 - 0.002 * 100 * 50 = 9_990.
            # Alice's margin fraction (mf) at this point is 5_000 / (100 * 100) = 0.5. Charlie's mf at this point is 9_980 / (100 * 50) = 1.996.
            await charlie.should_complete_fill_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("50"),
                Decimal("100"),
                Decimal("0"),
            )

            # Now, the index price moves to 145. The mark price here is 145. (Note that the precise liquidation price is 142.8571, however for the sake of round numbers the we send the price update of 145.)
            # Alice's mf at this point is (5_000 - 4_500) / (100 * 145) = 0.03448 (uh-oh!) where -4_500 is her unrealized pnl.
            # Bob's mf at this point is (9_980 + 2_250) / (50 * 145) = 1.6869 where +2_250 is his unrealized pnl.
            # Charlie's mf at this point is (9_980 + 2_250) / (50 * 145) = 1.6869 where +2_250 is his unrealized pnl.
            # Alice's mf is lower than the maintenance margin fraction (mmf) of 0.05! Alice will get liquidated.
            # Alice's bankruptcy price is 145 + (5_000 - 4_500) / 100 = 150. This mark price is the point at which Alice's total value of her positions is 0 (her unrealized pnl at this point would be -5_000, so her total value at this point would be 5_000 - 5_000 = 0).
            # Alice's position is attempted to be sold to the open market as a market order bid. However, there are no orders in the book and there remains a full balance of 100 <symbol> on the liquidated position. Thus, the exchange starts ADL'ing other positions by highest unrealized pnl first, position key second. There are two positions, Bob's long of 50 <symbol> and Charlie's long of 50 <symbol>.
            # Bob's long position is automatically closed by the exchange at the bankruptcy price of 150. Alice's realized pnl from her liquidated position is -2_500, and her collateral after Bob's position is closed is 5_000 - 2_500 = 2_500. Bob's realized pnl from his closed position is 2_500, and his collateral after his position is closed is 9_980 + 2_500 = 12_480. (Note: ADL'd traders do not incur any taker fees for their ADL.)
            # Charlie's long position is automatically closed by the exchange at the bankruptcy price of 150. Alice's realized pnl from her liquidated position is -2_500, and her collateral after Charlie's position is closed is 2_500 - 2_500 = 0. Charlie's realized pnl from his closed position is 2_500, and his collateral after his position is closed is 9_980 + 2_500 = 12_480. (Note: ADL'd traders do not incur any taker fees for their ADL.)
            # Since Alice's collateral at this point is 0, she has been fully liquidated. Bob has also been ADL'd and his long position closed by the exchange.
            current = await default_match_all_up_to(
                store.advance_until_liquidation_price(
                    tick_generator,
                    alice.position_ids[order_nonce],
                )
            )

            current.should_process_price_with_liquidations()
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. liquidations due to a new index price).


@pytest.mark.asyncio
async def test_liquidation_with_adl_from_max_taker_price_deviation(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("100"), Decimal("145"))},
            ),
            client,
        ) as tick_generator:
            # Alice deposits 5_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("5_000"))

            # Bob deposits 10_000 USDC.
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("10_000"))

            # Alice submits her first order (post).
            _, (order_nonce, _) = await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("100"),
                Decimal("100"),
                Decimal("0"),
            )

            # Bob submits his first order (match - complete fill).
            # Alice successfully opens a short position of 100 <symbol> for an entry price of 100 USDC. Bob successfully opens a long position of 100 <symbol> for an entry price of 100 USDC.
            # Bob incurs a taker fee, and so his collateral reduces to 10_000 - 0.002 * 100 * 100 = 9_980.
            # Alice's margin fraction (mf) at this point is 5_000 / (100 * 100) = 0.5. Bob's mf at this point is 9_980 / (100 * 100) = 0.998
            await bob.should_complete_fill_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("100"),
                Decimal("100"),
                Decimal("0"),
            )

            # Bob submits his second order (post). However, since 150 is greater than the max taker price deviation allowed price of 145.3225 * 1.02 = 148.2290, this order will not be matched. Thus, an ADL occurs, since there are no more orders in the book.
            await bob.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("100"),
                Decimal("150"),
                Decimal("0"),
            )

            # Now, the index price moves to 145. The mark price here is 145.3225. (Note that the precise liquidation price is 142.8571, however for the sake of round numbers the we send the price update of 145.)
            # Alice's mf at this point is (5_000 - 4_532.25) / (100 * 145.3225) = 0.03219 (uh-oh!) where -4_532.25 is her unrealized pnl.
            # Bob's mf at this point is (9_980 + 4_532.25) / (100 * 145.3225) = 0.9986 where +4_532.25 is her unrealized pnl.
            # Alice's mf is lower than the maintenance margin fraction (mmf) of 0.05! Alice will get liquidated.
            # Alice's bankruptcy price is 145.3225 + (5_000 - 4_532.25) / 100 = 150. This mark price is the point at which Alice's total value of her positions is 0 (her unrealized pnl at this point would be -5_000, so her total value at this point would be 5_000 - 5_000 = 0).
            # Alice's position is attempted to be sold to the open market as a market order bid. However, as explained above, there are no orders in the book that satisfy the max taker price deviation threshold and there remains a full balance of 100 <symbol> on the liquidated position. Thus, the exchange starts ADL'ing other positions by highest unrealized pnl first, position key second. However, in this case, there is only one position, Bob's long of 100 <symbol>.
            # Bob's long position is automatically closed by the exchange at the bankruptcy price of 150. Alice's realized pnl from her liquidated position is -5_000, and her collateral after Bob's position is closed is 5_000 - 5_000 = 0. Bob's realized pnl from his closed position is 5_000, and his collateral after his position is closed is 9_980 + 5_000 = 14_980. (Note: ADL'd traders do not incur any taker fees for their ADL.)
            # Since Alice's collateral at this point is 0, she has been fully liquidated. Bob has also been ADL'd and his long position closed by the exchange.
            current = await default_match_all_up_to(
                store.advance_until_liquidation_price(
                    tick_generator,
                    alice.position_ids[order_nonce],
                )
            )

            current.should_process_price_with_liquidations()
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. liquidations due to a new index price).


# TODO: add liquidation sale taker solvency guard test?


@pytest.mark.asyncio
async def test_liquidation_with_organic_adl_using_insurance_fund(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("100"), Decimal("155"))},
            ),
            client,
        ) as tick_generator:
            # Alice deposits 5_000 USDC.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("5_000"))

            # Bob deposits 10_000 USDC.
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("10_000"))

            # Alice submits her first order (post).
            _, (order_nonce, _) = await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("100"),
                Decimal("100"),
                Decimal("0"),
            )

            # Bob submits his first order (match - complete fill).
            # Alice successfully opens a short position of 100 <symbol> for an entry price of 100 USDC. Bob successfully opens a long position of 100 <symbol> for an entry price of 100 USDC.
            # Bob incurs a taker fee, and so his collateral reduces to 10_000 - 0.002 * 100 * 100 = 9_980.
            # Alice's margin fraction (mf) at this point is 5_000 / (100 * 100) = 0.5. Bob's mf at this point is 9_980 / (100 * 100) = 0.998.
            await bob.should_complete_fill_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("100"),
                Decimal("100"),
                Decimal("0"),
            )

            # Bob submits his second order (post). This order's price is barely within the max taker price deviation limit on the future mark price of 155.1935, 158.2974. However, as we will see, the total price delta drains the entire insurance fund organically, and begins ADLs. This is the "normal" catalyst situation for an ADL that most derivatives exchanges implement.
            await bob.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("100"),
                Decimal("158"),
                Decimal("0"),
            )

            # Now, the index price moves to 155. The mark price here is 155.1935. (Note that the precise liquidation price is 142.8571, however we send the price update of 155 to simulate a flash rally.)
            # Alice's mf at this point is (5_000 - 5_519.35) / (100 * 155.1935) = -0.03346 (uh-oh!) where -5_519 is her unrealized pnl. Note that due to the suddenness of the price movement, her total value is actually negative.
            # Bob's mf at this point is (9_980 + 5_519.35) / (100 * 155.1935) = 0.9987 where +5_519 is her unrealized pnl.
            # Alice's mf is lower than the maintenance margin fraction (mmf) of 0.05! Alice will get liquidated.
            # Alice's bankruptcy price is 155.1935 + (5_000 - 5_519.35) / 100 = 150. This mark price is the point at which Alice's total value of her positions is 0 (her unrealized pnl at this point would be -5_000, so her total value at this point would be 5_000 - 5_000 = 0).
            # Alice's position is sold to the open market as a market order bid. There is one potential taker, Bob, with an ask of 100 @ 158. As briefly mentioned above, this price is barely within the max taker price deviation of the mark price 155.1935, 159.2974. So this order is eligible for matching.
            # The price delta is negative, 150 - 158 = -8, meaning that, supposing we tried to sell Alice's entire position of 100, it would debit the insurance fund by -800. However, the insurance fund only has 20. Thus, the max we can actually fill the order is 20 / |-8| = 2.5. Bob gets partially filled, 2.5 @ 158. Alice's realized pnl from this at a bankruptcy price of 150 is -125, and her collateral becomes 5_000 - 125 = 4_875. Bob's realized pnl from this is 145, and his collateral becomes 9_980 + 145 = 10_125. (Note: takers of the liquidated position do not incur any taker fees.)
            # However, since there still remains a balance of 97.5 <symbol>, the exchange starts ADL'ing other positions by highest unrealized pnl first, position key second. However, in this case, there is only one position, Bob's long of (now) 97.5 <symbol>.
            # Bob's long position is automatically closed by the exchange at the bankruptcy price of 150. Alice's realized pnl from her liquidated position is -4_875, -20 of which gets taken from the insurance fund, draining it, and the remaining -4_855 deducted from her collateral. Her collateral after Bob's position is closed is 4_855 - 4_855 = 0. Bob's realized pnl from his closed position is 4_875, and his collateral after his position is closed is 10_125 + 4_875 = 15_000. (Note: ADL'd traders do not incur any taker fees for their ADL.)
            # The main criteria that was checked here was `insurance_fund_cap + liquidation_spread >= 0`, where `liquidation_spread = price_delta * fill_amount`. Here, liquidation_spread was positive since price_delta was positive, meaning that the exchange profited from the liquidation sale. Thus, insurance funds were not needed and were instead added to. However, if the liquidation_spread were negative (due to the price_delta being negative), funds from the organic insurance fund would be needed to cover losses on an immediate liquidation sale, subject to the above nonnegativity constraint. To satisfy this constraint it is sufficient to clamp the possible_fill_amount with a max fill amount of `insurance_fund_cap / |price_delta|` or less. For more details, see `derivadex/rust-packages/ddx-operator/enclave/src/execution/liquidation.rs`.
            # Finally, note that the fill amount undergoes a final check, Bob's solvency guard, and Bob successfully partially closes his long position of 100 <symbol> by 2.5 units and an exit price of 150 USDC. The other 97.5 units are ADL'd.
            # Alice's collateral at this point is 4_855 - 4_855 = 0. She has been fully liquidated. Bob's collateral at this point is 15_000 and his mf is 15_000 / (2.5 * 155.1935) = 38.6614.
            current = await default_match_all_up_to(
                store.advance_until_liquidation_price(
                    tick_generator,
                    alice.position_ids[order_nonce],
                )
            )

            current.should_process_price_with_liquidations()
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. liquidations due to a new index price).


@pytest.mark.asyncio
async def test_liquidation_self_match_with_adl(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1min",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("100"), Decimal("145"))},
            ),
            client,
        ) as tick_generator:
            # Alice deposits 5_000 USDC into main strategy.
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("5_000"))

            # Alice deposits 10_000 USDC into the alt strategy.
            await alice.should_deposit("alt", Decimal("10_000"))

            # Alice submits her first main strat order (post).
            _, (order_nonce, _) = await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("100"),
                Decimal("100"),
                Decimal("0"),
            )

            # Alice submits her first alt strat order (match - complete fill).
            # Alice maint successfully opens a short position of 100 <symbol> for an entry price of 100 USDC. Alice alt successfully opens a long position of 100 <symbol> for an entry price of 100 USDC.
            # Alice alt incurs a taker fee, and so collateral reduces to 10_000 - 0.002 * 100 * 100 = 9_980.
            # Alice main's margin fraction (mf) at this point is 5_000 / (100 * 100) = 0.5. Alice alt's mf at this point is 9_980 / (100 * 100) = 0.998.
            await alice.should_complete_fill_order(
                symbol,
                "alt",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("100"),
                Decimal("100"),
                Decimal("0"),
            )

            # Alice submits her second order (post). This is to set the stage for the "self match". We want to prevent against Alice's other soon-to-be liquidated positions to be included in the matching orders for her liquidation sale.
            await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("1"),
                Decimal("145"),
                Decimal("0"),
            )

            # Now, the index price moves to 145. The mark price here is 145. (Note that the precise liquidation price is 142.8571, however for the sake of round numbers the we send the price update of 145.)
            # Alice main's mf at this point is (5_000 - 4_500) / (100 * 145) = 0.03448 (uh-oh!) where -4_500 is her unrealized pnl.
            # Alice alt's mf at this point is (9_980 + 4_500) / (100 * 145) = 0.9986 where +4_500 is her unrealized pnl.
            # Alice main's mf is lower than the maintenance margin fraction (mmf) of 0.05! Alice main will get liquidated.
            # Alice main's bankruptcy price is 145 + (5_000 - 4_500) / 100 = 150. This mark price is the point at which Alice main's total value of her positions is 0 (her unrealized pnl at this point would be -5_000, so her total value at this point would be 5_000 - 5_000 = 0).
            # Alice main's position is attempted to be sold to the open market as a market order bid.
            # However, Alice main's other order to sell 1 @ 145 is the only one that theoretically could match her liquidated order. But since orders that belong to a trader who is currently in the process of being liquidated are not eligible to be matched, this order is not seen by the matching algorithm. Alice main's ask for 1 @ 145 will indeed be canceled at the end of the liquidation process as her entire strategy will have been liquidated, including all of her open orders.
            # But there are no more orders in the book and there still remains a full balance of 100 <symbol> on the liquidated position. Thus, the exchange starts ADL'ing other positions by highest unrealized pnl first, position key second. However, in this case, there is only one position, Alice alt's long of 100 <symbol>.
            # Alice alt's long position is automatically closed by the exchange at the bankruptcy price of 150. Alice main's realized pnl from her liquidated position is -5_000, and her collateral after Alice alt's position is closed is 5_000 - 5_000 = 0. Alice alt's realized pnl from his closed position is 5_000, and his collateral after his position is closed is 9_980 + 5_000 = 14_980. (Note: ADL'd traders do not incur any taker fees for their ADL.)
            # Since Alice main's collateral at this point is 0, main has been fully liquidated. Alice alt has also been ADL'd and his long position closed by the exchange.
            current = await default_match_all_up_to(
                store.advance_until_liquidation_price(
                    tick_generator,
                    alice.position_ids[order_nonce],
                )
            )

            current.should_process_price_with_liquidations()
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. liquidations due to a new index price).


@pytest.mark.asyncio
async def test_liquidation_with_adl_mul_symbols(
    symbol, underlying, symbol_2, underlying_2
):
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
                    symbol: (Decimal("100"), Decimal("290")),
                    symbol_2: (Decimal("200"), Decimal("290")),
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

            # Bob submits his first order (match - complete fill).
            # Alice successfully opens a short position of 0.1 <symbol> for an entry price of 100 USDC. Bob successfully opens a long position of 0.1 <symbol> for an entry price of 100 USDC.
            # Bob incurs a taker fee, and so his collateral reduces to 10_000 - 0.002 * 0.1 * 100 = 9_999.98.
            # Alice's margin fraction (mf) at this point is 10_000 / (0.1 * 100) = 1_000. Bob's mf at this point is 9_999.98 / (0.1 * 100) = 999.998.
            await bob.should_complete_fill_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("0.1"),
                Decimal("100"),
                Decimal("0"),
            )

            # Alice submits her second order (post).
            _, (order_nonce, _) = await alice.should_post_order(
                symbol_2,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("100"),
                Decimal("200"),
                Decimal("0"),
            )

            # Bob submits his second order (match - complete fill).
            # Alice successfully opens a short position of 100 <symbol_2> for an entry price of 200 USDC. Bob successfully opens a long position of 100 <symbol_2> for an entry price of 200 USDC.
            # Bob incurs a taker fee, and so his collateral reduces to 9_999.98 - 0.002 * 100 * 200 = 9_959.98.
            # Alice's mf at this point is 10_000 / (0.1 * 100 + 100 * 200) = 0.4998. Bob's mf at this point is 9_959.98 / (0.1 * 100 + 1 * 200) = 47.4285.
            await bob.should_complete_fill_order(
                symbol_2,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("100"),
                Decimal("200"),
                Decimal("0"),
            )

            # Now, both index prices moves to 290. The mark prices here are 290. (Note that the precise liquidation price of <symbol_2> is 285.7143 (assuming other prices stay constant), however for the sake of round numbers the we send the price update of 290.)
            # Alice's mf at this point is (10_000 - 19 - 9_000) / (0.1 * 290 + 100 * 290) = 0.03379 (uh-oh!) where -19 - 9_000 is her unrealized pnl.
            # Bob's mf at this point is (9_959.98 + 19 + 9_000) / (0.1 * 290 + 100 * 290) = 0.6538 where +19 + 9_000 is her unrealized pnl.
            # Alice's mf is lower than the maintenance margin fraction (mmf) of 0.05! Alice will get liquidated.
            # Alice's bankruptcy price for <symbol_2> is 290 + (10_000 - 19 - 9_000) / 100 = 299.81. This mark price of <symbol_2> is the point at which Alice's total value of her positions is 0 (her unrealized pnl at this point would be -19 - 9_981, so her total value at this point would be 10_000 - 19 - 9_981 = 0).
            # All of Alice's positions are attempted to be sold to the open market as market order bids. However, there are no orders in the book and there remains full balances of 0.1 <symbol> and 100 <symbol_2>. Thus, the exchange starts ADL'ing other positions by highest unrealized pnl first, position key second. Both of Bob's long positions of 0.1 <symbol> and 100 <symbol_2> are chosen for ADL.
            # Alice's short <symbol_2> position is liquidated first because it has the most negative unrealized pnl. Bob's long <symbol_2> position for the same amount is automatically closed by the exchange at the bankruptcy price of 299.81. Alice's realized pnl from her liquidated position is -9_981, and her collateral after Bob's position is closed is 10_000 - 9_981 = 19. Bob's realized pnl from his closed position is 9_981, and his collateral after his position is closed is 9_959.98 + 9_981 = 19_940.98. (Note: ADL'd traders do not incur any taker fees for their ADL.)
            # Next, Alice's short <symbol> position is liquidated. Bob's long <symbol> position for the same amount is automatically closed by the exchange at the bankruptcy price of <symbol> of 290 + (19 - 19) / 0.1 = 290. Alice's realized pnl from her liquidated position is -19, and her collateral after Bob's position is closed is 19 - 19 = 0. Bob's realized pnl from his closed position is 19, and his collateral after his position is closed is 19_940.98 + 19 = 19_959.98. (Note: ADL'd traders do not incur any taker fees for their ADL.)
            # Since Alice's collateral at this point is 0, she has been fully liquidated. Bob has also been ADL'd and his long positions closed by the exchange.
            current = await default_match_all_up_to(
                store.advance_until_liquidation_price(
                    tick_generator,
                    alice.position_ids[order_nonce],
                )
            )

            current.should_process_price_with_liquidations()
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. liquidations due to a new index price).


@pytest.mark.asyncio
async def test_fuzzed_liquidation_with_adl(symbol, underlying, random_seed):
    random.seed(random_seed)
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        price_range = (Decimal("990"), Decimal("1_010"))
        amount_range = (Decimal("1"), Decimal("4"))
        for _ in range(10):
            price, amount, side, order_type = (
                await FuzzedAccountMatcher.generate_fuzzed_order(
                    symbol, "main", amount_range, price_range, OrderType.Limit
                )
            )
            # Alice will get liquidated either way, but to make this happen we need to set the final price in the direction of liquidation.
            if side == OrderSide.Ask:
                to_price = Decimal("2_000")
            else:
                to_price = Decimal("1")

            logger.info(
                f"Running liquidation scenario with price: {price}, amount: {amount}, side: {side}, order_type: {order_type}, to_price: {to_price}"
            )
            async with store.run_scenario(
                CustomMarketDataDriver.from_price_ranges(
                    {symbol: underlying},
                    "1s",
                    client,
                    start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                    duration="1m",
                    price_ranges={symbol: (Decimal("1_000"), to_price)},
                ),
                client,
            ) as tick_generator:
                # Alice deposits 10_000 USDC
                alice = FuzzedAccountMatcher(Account(store.wallet.account_for_index(0)))
                await alice.should_deposit("main", Decimal("1_000"))

                # Bob deposits 10_000 USDC
                bob = FuzzedAccountMatcher(Account(store.wallet.account_for_index(1)))
                await bob.should_deposit("main", Decimal("1_000"))

                # Alice submits her order.
                _, (order_nonce, _) = await alice.should_post_order(
                    symbol,
                    "main",
                    side,
                    order_type,
                    amount,
                    price,
                    Decimal("0"),
                )

                # Bob submits his order (match).
                await bob.should_complete_or_partial_fill_order(
                    symbol,
                    "main",
                    OrderSide.Bid if side == OrderSide.Ask else OrderSide.Ask,
                    OrderType.Limit,
                    amount,
                    price,
                    Decimal("0"),
                )

                # Alice will be liquidated.
                current = await default_match_all_up_to(
                    store.advance_until_liquidation_price(
                        tick_generator,
                        alice.position_ids[order_nonce],
                    )
                )

                current.should_process_price_with_liquidations()
                current.default_match_rest()
                # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. liquidations due to a new index price).


# Issue #3989: https://gitlab.com/dexlabs/derivadex/-/issues/3989
@pytest.mark.asyncio
async def test_rolling_price_ordinal_updates_correctly(symbol, underlying):
    async with aiohttp.ClientSession() as client:
        store: Store = Store.the_store()
        async with store.run_scenario(
            CustomMarketDataDriver.from_price_ranges(
                {symbol: underlying},
                "1s",
                client,
                start_timestamp=pd.Timestamp("2023-03-29T07:00:00"),
                duration="1m",
                price_ranges={symbol: (Decimal("1_000"), Decimal("2_000"))},
            ),
            client,
        ) as tick_generator:
            # Alice deposits 10_000 USDC
            alice = AccountMatcher(Account(store.wallet.account_for_index(0)))
            await alice.should_deposit("main", Decimal("1_000"))

            # Bob deposits 10_000 USDC
            bob = AccountMatcher(Account(store.wallet.account_for_index(1)))
            await bob.should_deposit("main", Decimal("1_000"))

            # Alice submits her order.
            _, (order_nonce, _) = await alice.should_post_order(
                symbol,
                "main",
                OrderSide.Ask,
                OrderType.Limit,
                Decimal("1.2481"),
                Decimal("998.438497"),
                Decimal("0"),
            )

            # Bob submits his order (match).
            await bob.should_complete_or_partial_fill_order(
                symbol,
                "main",
                OrderSide.Bid,
                OrderType.Limit,
                Decimal("1.2481"),
                Decimal("998.438497"),
                Decimal("0"),
            )

            # Alice will be liquidated.
            current = await default_match_all_up_to(
                store.advance_until_liquidation_price(
                    tick_generator,
                    alice.position_ids[order_nonce],
                )
            )

            current.should_process_price_with_liquidations()
            current.default_match_rest()
            # If there are no assertion errors here, the auditor will verify the state (account) equality of the reference state with the actual state (i.e. liquidations due to a new index price).


# TODO: other insurance fund cases here?


all_tests = [
    test_liquidation_no_adl,
    test_liquidation_no_adl_negative_margin_fraction,
    test_mul_liquidations_vs_same_maker_order_no_adl,
    test_liquidation_self_match_no_adl,
    test_liquidation_no_adl_using_insurance_fund,
    test_liquidation_with_adl_strategy_collision,
    test_liquidation_with_adl,
    test_liquidation_with_mul_adl,
    test_liquidation_with_adl_from_max_taker_price_deviation,
    test_liquidation_with_organic_adl_using_insurance_fund,
    test_liquidation_self_match_with_adl,
    test_liquidation_with_adl_mul_symbols,
    test_fuzzed_liquidation_with_adl,
    test_rolling_price_ordinal_updates_correctly,
]
