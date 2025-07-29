"""
DerivaDEX WebSocket Market Data Example

This script demonstrates how to:
1. Initialize the DerivaDEX client with WebSocket connection
2. Subscribe to real-time order book (L2) updates for ETHP
3. Subscribe to real-time mark price updates for ETHP
4. Process and display the incoming data

Prerequisites:
- Create a config.json file with your configuration:
{
    "webserver_url": "https://testnet.derivadex.io",
    "rpc_url": "<your_eth_rpc_url>",
    "contract_deployment": "testnet",
    "private_key": "<your_0x_prefixed_private_key>"
}

Usage:
$ python ddx_websocket_example.py --config config.json
"""

import asyncio
import json
import signal
from pathlib import Path
import configargparse
from datetime import datetime

from ddx.derivadex_client import DerivaDEXClient
from ddx.realtime_client.models import (
    Feed,
    FeedWithParams,
    MarkPriceParams,
    OrderBookL2Params,
    OrderBookL2Contents,
    MarkPriceContents,
)

# Symbol to track
SYMBOL = "ETHP"


def parse_args():
    """Parse command line arguments and load configuration"""
    parser = configargparse.ArgParser(description="DerivaDEX WebSocket Example")
    parser.add_argument(
        "-c", "--config", required=True, help="Path to config.json file"
    )

    options = parser.parse_args()

    with open(Path(options.config)) as fp:
        config = json.load(fp)

    return config


# Callback handlers for each feed type
def handle_order_book(contents: OrderBookL2Contents):
    """Process order book update every time there is new data"""

    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] Handling Order Book Update: {contents}")


def handle_mark_price(contents: MarkPriceContents):
    """Process mark price update every time there is no data"""

    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] Handling Mark Price Update: {contents}")


async def main():
    """Main function to demonstrate WebSocket subscription and processing"""
    # Load configuration
    config = parse_args()

    # Flag to control the main loop
    running = True

    # Setup signal handlers for graceful shutdown
    def signal_handler():
        nonlocal running
        print("\nShutdown signal received. Closing connections...")
        running = False

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    print(f"Initializing DerivaDEX client and subscribing to {SYMBOL} market data...")

    # Initialize the client with context manager to ensure proper cleanup
    async with DerivaDEXClient(
        base_url=config["webserver_url"],
        rpc_url=config["rpc_url"],
        contract_deployment=config["contract_deployment"],
        private_key=config["private_key"],
    ) as client:
        print("Connected to DerivaDEX")

        # Subscribe to the feeds with their respective callbacks
        await client.ws.subscribe_feeds(
            [
                # Order book L2 feed with parameters and callback
                (
                    FeedWithParams(
                        feed=Feed.ORDER_BOOK_L2,
                        params=OrderBookL2Params(symbol=SYMBOL, aggregation=0.1),
                    ),
                    handle_order_book,
                ),
                # Mark price feed with parameters and callback
                (
                    FeedWithParams(
                        feed=Feed.MARK_PRICE, params=MarkPriceParams(symbols=[SYMBOL])
                    ),
                    handle_mark_price,
                ),
            ]
        )

        print(f"Subscribed to {SYMBOL} market data feeds")
        print("Receiving real-time updates (press Ctrl+C to exit)...")

        # Keep the program running until interrupted
        while running:
            # Check current state periodically
            if client.ws.mark_price(SYMBOL):
                current_price = client.ws.mark_price(SYMBOL)
                print(f"Current {SYMBOL} Mark Price: {current_price}")

            # Sleep to avoid CPU spinning
            await asyncio.sleep(10)

        print("Shutting down...")


if __name__ == "__main__":
    asyncio.run(main())
