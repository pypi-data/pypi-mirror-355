"""
Sample DerivaDEX chaos bot
"""

import asyncio
import logging
import os
from typing import Dict

import jsonschema
from whitebox_fuzzing.test_utils.test_derivadex_client import TestDerivaDEXClient
from ddx.sample_strategies.chaos_strategies.spawner import Spawner
from utils.utils import get_config
from ddx._rust.decimal import Decimal

fmt_str = "[%(asctime)s] %(levelname)s @ line %(lineno)d: %(message)s"
log_level = os.environ.get("PYTHON_LOG").upper() if "PYTHON_LOG" in os.environ else 100
logging.basicConfig(level=log_level, format=fmt_str)
logger = logging.getLogger(__name__)


async def main(config_json: Dict):
    """
    Main entry point for chaos testing system.

    Parameters
    ----------
    config_json : Dict
        Chaos bot configuration including connection details and test parameters
    """

    # Initialize client with new pattern
    async with TestDerivaDEXClient(
        base_url=config_json["webserver_url"],
        rpc_url=config_json["rpc_url"],
        contract_deployment=config_json["contract_deployment"],
        private_key=config_json["private_key"],
    ) as client:
        # Setup WebSocket subscriptions
        await client.ws.subscribe(feed="MARK_PRICE")

        deployment_info = await client.config.get_deployment_info(
            config_json["contract_deployment"]
        )

        # Initialize spawner with updated client
        spawner = Spawner(
            client,
            deployment_info.addresses.usdc_address,
            Decimal(str(config_json["deposit_amount"])),
            config_json["chaos_strategy"],
            config_json["markets"],
            config_json["strategies"],
            ddx_address=deployment_info.addresses.ddx_address,
            ddx_faucet_key=config_json.get("faucet_private_key"),
            sleep_rate=config_json["sleep_rate"],
        )

    bot_tasks = set()
    for i in range(config_json["num_accounts"]):
        logger.info("spawning a new bot")
        bot = spawner.spawn()
        task = asyncio.create_task(bot.run())
        bot_tasks.add(task)
        task.add_done_callback(bot_tasks.discard)
        await asyncio.sleep(0)

    while len(bot_tasks) > 0:
        logger.info(f"{len(bot_tasks)} bots are running")
        await asyncio.sleep(5)


if __name__ == "__main__":
    config_json = get_config("chaos")

    chaos_schema = {
        "type": "object",
        "properties": {
            "webserver_url": {"type": "string"},
            "contract_deployment": {"type": "string"},
            "rpc_url": {"type": "string"},
            "deposit_amount": {"type": "number"},
            "sleep_rate": {"type": "number"},
            "num_accounts": {"type": "number"},
            "bot_address": {"type": "string"},
            "private_key": {"type": "string"},
            "chaos_strategy": {"type": "string"},
            "markets": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "quantity": {"type": "number"},
                    },
                    "minProperties": 2,
                },
                "minItems": 1,
                "uniqueItems": True,
            },
            "strategies": {
                "type": "array",
                "items": {
                    "type": "string",
                },
                "minItems": 1,
                "uniqueItems": True,
            },
        },
        "minProperties": 11,
    }

    jsonschema.validate(config_json, chaos_schema)

    asyncio.run(main(config_json))
