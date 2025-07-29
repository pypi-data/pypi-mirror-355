"""
DerivaDEX Deposit USDC Example

This script demonstrates how to:
1. Initialize the DerivaDEX client
2. View available collateral in a Strategy
3. Deposit USDC on-chain to the DerivaDEX network

Configuration:
Create a config.json file with your configuration:
{
    "webserver_url": "https://testnet.derivadex.io",
    "rpc_url": "<your_eth_rpc_url>",
    "contract_deployment": "testnet",
    "private_key": "<your_0x_prefixed_private_key>"
}

Notes:
- Have some ETH in your wallet for gas
- Have USDC in your wallet to deposit

Usage:
$ python deposit_usdc.py --config config.json
"""


import asyncio
import json
from pathlib import Path
import configargparse

from ddx._rust.decimal import Decimal

from ddx.derivadex_client import DerivaDEXClient


# Strategy ID to deposit into
STRATEGY_ID = "main"

# Amount to deposit (in USDC)
DEPOSIT_AMOUNT = Decimal("1_000.0")


def parse_args():
    """Parse command line arguments and load configuration"""
    parser = configargparse.ArgParser(description="DerivaDEX Deposit Example")
    parser.add_argument(
        "-c", "--config", required=True, help="Path to config.json file"
    )

    options = parser.parse_args()

    with open(Path(options.config)) as fp:
        config = json.load(fp)

    return config


async def main():
    """Main function to execute the deposit flow"""
    # Load configuration
    config = parse_args()

    print("Initializing DerivaDEX client...")
    async with DerivaDEXClient(
        base_url=config["webserver_url"],
        rpc_url=config["rpc_url"],
        contract_deployment=config["contract_deployment"],
        private_key=config["private_key"],
    ) as client:
        # Get trader address
        trader_address = client.web3_account.address
        print(f"Connected as trader: {trader_address}")

        # Get deployment info to find USDC address
        deployment_info = await client.system.get_deployment_info(
            config["contract_deployment"]
        )
        usdc_address = deployment_info.addresses.usdc_address
        print(f"Using USDC contract: {usdc_address}")

        # Check current collateral balance (likely 0, assuming never having deposited)
        strategy_response = await client.account.get_strategy(
            trader_address, STRATEGY_ID
        )
        try:
            print(
                f"Current strategy collateral: {strategy_response.value.avail_collateral} USDC"
            )
        except AttributeError:
            print(f"Current strategy collateral: 0 USDC")

        # Approve USDC for deposit
        print(f"Approving {DEPOSIT_AMOUNT} USDC for deposit...")
        approval_tx_receipt = client.on_chain.approve(usdc_address, DEPOSIT_AMOUNT)
        print(f"Approval transaction hash: {approval_tx_receipt.transactionHash.hex()}")

        # Deposit USDC into the strategy
        print(f"Depositing {DEPOSIT_AMOUNT} USDC into strategy '{STRATEGY_ID}'...")
        deposit_tx_receipt = await client.on_chain.deposit(
            usdc_address, STRATEGY_ID, DEPOSIT_AMOUNT
        )
        print(f"Deposit transaction hash: {deposit_tx_receipt.transactionHash.hex()}")

        # Wait for 6 confirmations
        print("Waiting for 6 block confirmations...")
        await client.on_chain.wait_for_confirmations(deposit_tx_receipt)
        print("Deposit confirmed!")

        # This is a bit annoying, but perhaps nothing we can really do...
        await asyncio.sleep(20)

        # Check updated collateral balance
        strategy_response = await client.account.get_strategy(
            trader_address, STRATEGY_ID
        )
        print(
            f"Updated strategy collateral: {strategy_response.value.avail_collateral} USDC"
        )


if __name__ == "__main__":
    asyncio.run(main())
