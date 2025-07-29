"""
DerivaDEX REST API Quickstart Example

This script demonstrates how to:
1. Initialize the DerivaDEX client
2. View strategy information and metrics
3. Place a market sell order for ETH
4. Get the current mark price and place a limit buy order 5% below it
5. Cancel the limit order

Prerequisites:
- You have already deposited funds into your strategy
- Create a config.json file with your configuration:
{
    "webserver_url": "https://testnet.derivadex.io",
    "rpc_url": "<your_eth_rpc_url>",
    "contract_deployment": "testnet",
    "private_key": "<your_0x_prefixed_private_key>"
}

Usage:
$ python ddx_rest_quickstart.py --config config.json
"""

import asyncio
import json
from pathlib import Path
import configargparse

from ddx._rust.common.enums import OrderSide, OrderType
from ddx._rust.common.requests.intents import (
    OrderIntent,
    CancelOrderIntent,
    CancelAllIntent,
)
from ddx._rust.common.state.keys import StrategyKey
from ddx._rust.decimal import Decimal

from ddx.derivadex_client import DerivaDEXClient
from utils.utils import round_to_unit

# Strategy ID to trade with
STRATEGY_ID = "main"

# Trading symbol
SYMBOL = "ETHP"

# Amount to trade (in ETH)
TRADE_AMOUNT = Decimal("0.1")


def parse_args():
    """Parse command line arguments and load configuration"""
    parser = configargparse.ArgParser(description="DerivaDEX REST API Quickstart")
    parser.add_argument(
        "-c", "--config", required=True, help="Path to config.json file"
    )

    options = parser.parse_args()

    with open(Path(options.config)) as fp:
        config = json.load(fp)

    return config


async def main():
    """Main function to execute the trading flow"""
    # Load configuration
    config = parse_args()

    # Step 1: Initialize the DerivaDEX client
    print("Initializing DerivaDEX client...")
    async with DerivaDEXClient(
        base_url=config["webserver_url"],
        rpc_url=config["rpc_url"],
        contract_deployment=config["contract_deployment"],
        private_key=config["private_key"],
    ) as client:
        # Get trader address
        trader_address = client.web3_account.address
        trader_address_with_prefix = f"0x00{trader_address[2:]}"
        print(f"Connected as trader: {trader_address}")

        # Step 2: Get strategy information and metrics
        print(f"Fetching strategy information for '{STRATEGY_ID}'...")
        strategy_response = await client.account.get_strategy(
            trader_address, STRATEGY_ID
        )
        print(f"Strategy: {strategy_response.model_dump()}")

        # Step 3: Place a market sell order for ETH
        print(f"Placing market sell order for {TRADE_AMOUNT} {SYMBOL}...")

        # Create the market sell order intent
        market_order_intent = OrderIntent(
            SYMBOL,  # Symbol
            STRATEGY_ID,  # Strategy ID
            OrderSide.Ask,  # Order side
            OrderType.Market,  # Order type
            client.trade.get_nonce(),  # Unique nonce
            TRADE_AMOUNT,  # Order amount
            Decimal("0"),  # Order price (0 for market)
            Decimal("0"),  # Stop price (0 for currently unsupported)
            None,  # Session key signature
        )

        # Submit the market order
        market_order_recipient = await client.trade.place_order(market_order_intent)
        print(f"Market order submitted: {market_order_recipient.model_dump()}")

        # Step 4: Get current mark price and place limit buy order 5% below
        print(f"Fetching current mark price for {SYMBOL}...")

        mark_price_history_response = await client.market.get_mark_price_history_page(
            "ETHP", limit=20
        )
        # Get the latest mark price for the symbol
        current_price = Decimal(mark_price_history_response.value[0].price)
        print(f"Current {SYMBOL} price: {current_price}")

        # Calculate price 5% below current price
        limit_price = round_to_unit(current_price * Decimal("0.95"), 1)
        print(f"Placing limit buy order at {limit_price} USDC (5% below market)")

        # Create the market sell order intent
        limit_order_intent = OrderIntent(
            SYMBOL,  # Symbol
            STRATEGY_ID,  # Strategy ID
            OrderSide.Bid,  # Order side
            OrderType.Limit,  # Order type
            client.trade.get_nonce(),  # Unique nonce
            TRADE_AMOUNT,  # Order amount
            limit_price,  # Order price
            Decimal("0"),  # Stop price (0 for currently unsupported)
            None,  # Session key signature
        )

        # Submit the limit order
        limit_order_receipt = await client.trade.place_order(limit_order_intent)
        print(f"Limit order submitted: {limit_order_receipt.model_dump()}")

        # Step 5: Cancel the limit order
        # Extract order hash from the response for cancellation
        order_hash = limit_order_intent.hash()
        print(f"Cancelling limit order: {order_hash}")

        # Create the cancel order intent
        cancel_order_intent = CancelOrderIntent(
            SYMBOL,
            order_hash,
            client.trade.get_nonce(),
            None,
        )

        # Submit the cancel request
        cancel_order_receipt = await client.trade.cancel_order(cancel_order_intent)
        print(f"Cancel request submitted: {cancel_order_receipt.model_dump()}")


if __name__ == "__main__":
    asyncio.run(main())
