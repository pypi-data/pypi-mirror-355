"""
Sample DerivaDEX market making
"""

import asyncio
import logging
import random
from os import environ
from typing import Dict, Optional

import jsonschema
from attrs import define, field
from ddx.derivadex_client import DerivaDEXClient
from utils.utils import (
    exchange_is_up,
    get_config,
    get_contract_deployment_info,
    round_to_unit,
)
from ddx._rust.common import ProductSymbol
from ddx._rust.common.enums import OrderSide, OrderType
from ddx._rust.common.requests.intents import CancelAllIntent, OrderIntent
from ddx._rust.common.state.keys import StrategyKey
from ddx._rust.decimal import Decimal

fmt_str = "[%(asctime)s] %(levelname)s @ line %(lineno)d: %(message)s"
log_level = environ.get("PYTHON_LOG").upper() if "PYTHON_LOG" in environ else 100
logging.basicConfig(level=log_level, format=fmt_str)
logger = logging.getLogger(__name__)


@define
class Trader:
    """
    Defines a Trader

    A Trader contains information pertaining to a trader's data.

    Attributes:
        avail_ddx (Decimal): available DDX balance
        locked_ddx (Decimal): locked DDX balance available for on-chain withdrawal
        pay_fees_in_ddx (bool): whether trader has opted in to pay fees in DDX
    """

    avail_ddx: Decimal
    locked_ddx: Decimal
    pay_fees_in_ddx: bool


@define
class Strategy:
    """
    Defines a Strategy

    A Strategy contains information pertaining to a trader's
    cross-margined strategy, such as their free and frozen collaterals
    and max leverage.

    Attributes:
        strategy_id (str): Identifier for strategy
        avail_collateral (Dict[str, Decimal]): collateral address <> collateral value indicating the collateral available for trading
        locked_collateral (Dict[str, Decimal]): collateral address <> collateral value indicating the collateral available for on-chain withdrawal
        max_leverage (int): Max leverage the strategy can take
        frozen (bool): Whether the strategy is frozen or not (relevant for tokenization)
    """

    strategy_id: str = field(eq=str.lower)
    avail_collateral: Dict[str, Decimal]
    locked_collateral: Dict[str, Decimal]
    max_leverage: int
    frozen: bool


def create_maker_limit_order_intent(
    derivadex_client: DerivaDEXClient,
    symbol: ProductSymbol,
    strategy: str,
    base_px: Decimal,
    side: OrderSide,
    price_offset_index: int,
    price_offset: Decimal,
    quantity_per_level: Decimal,
) -> OrderIntent:
    """
    Create a maker limit order

    Parameters
    ----------
    derivadex_client : DerivaDEXClient
        DerivaDEX client wrapper
    symbol : str
        Market symbol
    strategy : str
        Trader strategy
    base_px : Decimal
        Base price to adjust with offsets
    side : str
        Order side - "Bid" or "Ask"
    price_offset_index : int
        Level offset to determine price adjustment to base price
    price_offset : Decimal
        Specifies price between quoted levels
    quantity_per_level : Decimal
        Size to post for each quoted level

    Returns
    -------
    OrderIntent
        Signed order intent to be placed
    """

    price = round_to_unit(
        (
            base_px
            * (Decimal("1") - price_offset * (price_offset_index + Decimal("1")))
            if side == OrderSide.Bid
            else base_px
            * (Decimal("1") + price_offset * (price_offset_index + Decimal("1")))
        ),
        1 if symbol == "ETHP" else 0,
    )

    quantity = round_to_unit(
        Decimal(
            str(
                random.uniform(
                    float(quantity_per_level - quantity_per_level / Decimal("2")),
                    float(quantity_per_level + quantity_per_level / Decimal("2")),
                )
            )
        ),
        1,
    )

    return OrderIntent(
        symbol,
        strategy,
        side,
        OrderType.Limit,
        f"0x{derivadex_client.get_encoded_nonce()}",
        quantity,
        price,
        Decimal("0"),
        None,
    )


def should_revisit_orders(
    mark_price: Decimal,
    ref_px_deviation_to_replace_orders: Decimal,
    deployment: str,
    ref_mark_px: Optional[Decimal] = None,
) -> bool:
    """
    Checks whether bot should revisit/refresh orders

    Parameters
    ----------
    mark_price : Decimal
        Latest mark price for market
    ref_px_deviation_to_replace_orders : Decimal
        Specifies how much the reference price must change to
        refresh orders
    deployment : str
        Deployment name
    ref_mark_px : Decimal
        Reference mark price for market

    Returns
    -------
    bool
        Whether bot should refresh orders
    """

    if (
        deployment == "geth"
        or ref_mark_px is None
        or abs((mark_price - ref_mark_px) / ref_mark_px)
        > ref_px_deviation_to_replace_orders
    ):
        logging.info(
            f"REFRESH: mark_price ({mark_price}) drifted from ref_mark_px ({ref_mark_px})"
        )
        return True
    return False


async def cancel_orders(
    derivadex_client: DerivaDEXClient, symbol_to_cancel: str, strategy: str
):
    """
    Cancel active open orders

    Parameters
    ----------
    derivadex_client : DerivaDEXClient
        DerivaDEX client wrapper
    symbol_to_cancel: str
        Symbol to cancel
    strategy: str
        Strategy we want to cancel orders for
    """

    logging.info(f"CANCEL_ALL: canceling all")
    cancel_all_intent = CancelAllIntent(
        symbol_to_cancel,
        strategy,
        f"0x{derivadex_client.get_encoded_nonce()}",
        None,
    )
    await derivadex_client.cancel_all_orders(cancel_all_intent)


async def place_orders(
    derivadex_client: DerivaDEXClient,
    symbol: ProductSymbol,
    strategy: str,
    base_px: Decimal,
    levels_to_quote: int,
    price_offset: Decimal,
    quantity_per_level: Decimal,
    max_position_size: Decimal,
):
    """
    Place new orders around a base price

    Parameters
    ----------
    derivadex_client : DerivaDEXClient
        DerivaDEX client wrapper
    symbol : str
        Market symbol
    strategy : str
        Trader strategy
    base_px : Decimal
        Base price to adjust with offsets
    levels_to_quote : int
        Number of levels on either side to quote
    price_offset : Decimal
        Specifies price between quoted levels
    quantity_per_level : Decimal
        Size to post for each quoted level
    max_position_size : Decimal
        Max position size
    """

    order_intents = []

    latest_position = await derivadex_client.websocket.get_positions(symbol)

    bid_allowed = (
        latest_position is None
        or latest_position.side == "Short"
        or latest_position.balance < max_position_size
    )
    ask_allowed = (
        latest_position is None
        or latest_position.side == "Long"
        or latest_position.balance < max_position_size
    )

    # Iterate through the levels to quote
    for level in range(levels_to_quote):
        # Create a new bid order intent for level
        if bid_allowed:
            bid_order_intent = create_maker_limit_order_intent(
                derivadex_client,
                symbol,
                strategy,
                base_px,
                OrderSide.Bid,
                level,
                price_offset,
                quantity_per_level,
            )
            logging.info(
                f"POST: symbol = {symbol}, strategy = {strategy}, side = {bid_order_intent.side}; amount = {bid_order_intent.amount}; price = {bid_order_intent.price}"
            )
            order_intents.append(bid_order_intent)

        if ask_allowed:
            # Create a new ask order intent for level.
            ask_order_intent = create_maker_limit_order_intent(
                derivadex_client,
                symbol,
                strategy,
                base_px,
                OrderSide.Ask,
                level,
                price_offset,
                quantity_per_level,
            )
            logging.info(
                f"POST: symbol = {symbol}, strategy = {strategy}, side = {ask_order_intent.side}; amount = {ask_order_intent.amount}; price = {ask_order_intent.price}"
            )
            order_intents.append(ask_order_intent)

    # Submit created orders to the Operator for placement.
    await derivadex_client.create_orders(order_intents)


async def deposit_if_necessary(
    derivadex_client: DerivaDEXClient,
    collateral_address: str,
    ddx_address: str,
    deposit_minimum: Decimal,
    deposit_amount: Decimal,
    faucet_private_key: str,
    strategy: str,
):
    trader_leaf = await get_trader(derivadex_client)
    strategy_leaf = await get_strategy(derivadex_client, collateral_address, strategy)

    deposited = False
    while (
        strategy_leaf is None
        or collateral_address not in strategy_leaf.avail_collateral
        or strategy_leaf.avail_collateral[collateral_address] < deposit_minimum
    ):
        if not deposited and strategy_leaf is not None:
            logging.info(f"Depositing for strategy: {strategy}")
            nonce = derivadex_client.w3.eth.get_transaction_count(
                derivadex_client.web3_account.address
            )
            if faucet_private_key is not None and (
                trader_leaf is None or trader_leaf.avail_ddx < Decimal("1_000_000")
            ):
                await derivadex_client.mint_ddx(
                    ddx_address, faucet_private_key, Decimal("1_000_000")
                )
                logging.info("finished mint ddx")
                await derivadex_client.approve_ddx(
                    ddx_address, Decimal("1_000_000"), nonce=nonce
                )
                logging.info("finished approve ddx")
                await derivadex_client.deposit_ddx(
                    Decimal("1_000_000"), nonce=nonce + 1
                )
                logging.info("finished deposit ddx")
                nonce += 2
            await derivadex_client.mint(collateral_address, deposit_amount, nonce=nonce)
            logging.info("finished mint")
            await derivadex_client.approve(
                collateral_address, deposit_amount, nonce=nonce + 1
            )
            logging.info("finished approve")
            # await derivadex_client.deposit(
            #     collateral_address, strategy, deposit_amount, nonce=nonce + 2
            # )
            # logging.info(f"deposited for {strategy}")
            deposited = True

        logging.info("DEPOSIT: must deposit sufficient capital")
        await asyncio.sleep(5)
        trader_leaf = await get_trader(derivadex_client)
        strategy_leaf = await get_strategy(
            derivadex_client, collateral_address, strategy
        )
        if strategy_leaf is None:
            logging.info(f"Haven't found strategy leaf still for {strategy}")
    if deposited:
        logging.info(
            "DEPOSIT: sufficient collateral for strategy {strategy} has been deposited"
        )


async def get_trader(
    derivadex_client: DerivaDEXClient,
):
    trader = await derivadex_client.get_trader(
        f"0x{derivadex_client.web3_account.address.lower()[2:]}"
    )

    if trader is not None and "value" in trader:
        return Trader(
            Decimal(trader["value"]["availDdx"]),
            Decimal(trader["value"]["lockedDdx"]),
            trader["value"]["payFeesInDdx"],
        )
    elif trader is not None:
        return Trader(
            Decimal("0"),
            Decimal("0"),
            False,
        )
    return None


async def get_strategy(
    derivadex_client: DerivaDEXClient,
    collateral_address: str,
    strategy_str: str,
):
    strategy = await derivadex_client.get_strategy(
        f"0x{derivadex_client.web3_account.address.lower()[2:]}", strategy_str
    )

    logging.info(f"Strategy: {strategy}")
    if strategy is not None and "value" in strategy:
        return Strategy(
            strategy["value"]["strategyId"],
            {
                collateral_address: Decimal(
                    strategy["value"]["availCollateral"],
                )
            },
            {
                collateral_address: Decimal(
                    strategy["value"]["lockedCollateral"],
                )
            },
            int(strategy["value"]["maxLeverage"]),
            strategy["value"]["frozen"],
        )
    elif strategy is not None:
        return Strategy(
            strategy_str,
            {},
            {},
            3,
            False,
        )
    return None


async def main(
    config_json: Dict,
):
    """
    Main entry point for sample market making strategy

    Parameters
    ----------
    config_json : Dict
        Market maker config
    """

    if not exchange_is_up(
        config_json["webserver_url"], config_json["contract_deployment"]
    ):
        # If exchange is not up yet...

        raise RuntimeError(f"exchange at {config_json['webserver_url']} is not up")

    deployment_info = get_contract_deployment_info(
        config_json["webserver_url"], config_json["contract_deployment"]
    )
    chain_id = deployment_info["chainId"]
    verifying_contract = deployment_info["addresses"]["derivaDEXAddress"]
    collateral_address = deployment_info["addresses"]["usdcAddress"]
    ddx_address = deployment_info["addresses"]["ddxAddress"]
    faucet_private_key = (
        config_json["faucet_private_key"]
        if "faucet_private_key" in config_json
        else None
    )

    # Get all symbols.
    symbols = [market["symbol"] for market in config_json["markets"]]

    # Initialize a client wrapper (REST and WS).
    derivadex_client = DerivaDEXClient(
        config_json["webserver_url"],
        config_json["rpc_url"],
        config_json["contract_deployment"],
        chain_id,
        verifying_contract,
        private_key=config_json["private_key"],
    )

    ref_mark_pxs = {symbol: None for symbol in symbols}

    while True:
        strategy = random.choice(config_json["strategies"])
        if not derivadex_client.websocket.connected:
            # Connect to the WS endpoint.
            await derivadex_client.websocket.connect()

            await derivadex_client.websocket.subscribe(
                [
                    {"feed": "MARK_PRICE", "params": {}},
                    {
                        "feed": "POSITION",
                        "params": {
                            "trader": f"0x00{derivadex_client.web3_account.address[2:]}",
                            "strategyIdHash": StrategyKey.generate_strategy_id_hash(
                                strategy
                            ),
                        },
                    },
                ]
            )

        try:
            await deposit_if_necessary(
                derivadex_client,
                collateral_address,
                ddx_address,
                config_json["deposit_minimum"],
                config_json["deposit_amount"],
                faucet_private_key,
                strategy,
            )
        except Exception as e:
            logging.info(f"Deposit if necessary exception: {e}")

        # Select random market.
        market = random.choice(config_json["markets"])
        symbol = market["symbol"]

        # Subscribe or retrieve latest price from WS.
        latest_price = await derivadex_client.websocket.get_prices(market["symbol"])

        if latest_price and should_revisit_orders(
            latest_price,
            market["ref_px_deviation_to_replace_orders"],
            config_json["contract_deployment"],
            ref_mark_pxs[symbol],
        ):
            # If latest price exists and we should refresh orders...

            ref_mark_pxs[market["symbol"]] = latest_price

            # Cancel all orders first to refresh new ones.
            await cancel_orders(derivadex_client, market["symbol"], strategy)

            # Random 20pt offset in either direction to trigger matches.
            if market["trading_strategy"] == "MAKER":
                base_px = latest_price
            elif market["trading_strategy"] == "TAKER":
                base_px = Decimal(
                    str(
                        random.uniform(
                            float(latest_price - Decimal("20")),
                            float(latest_price + Decimal("20")),
                        )
                    )
                )
            else:
                base_px = Decimal(
                    str(
                        random.uniform(
                            float(latest_price * Decimal("0.97")),
                            float(latest_price * Decimal("1.03")),
                        )
                    )
                )

            # Black out period, bot stops providing liquidity.
            if market["trading_strategy"] == "FUZZED" and random.random() < 0.01:
                logging.info(f"BLACK_OUT PERIOD...")
                await asyncio.sleep(30.0)

            if base_px > Decimal("0"):
                await place_orders(
                    derivadex_client,
                    market["symbol"],
                    strategy,
                    base_px,
                    market["levels_to_quote"],
                    market["price_offset"],
                    market["quantity_per_level"],
                    market["max_position_size"],
                )

        await asyncio.sleep(config_json["sleep_rate"])


if __name__ == "__main__":
    config_json = get_config("marketmaker")
    mm_schema = {
        "type": "object",
        "properties": {
            "webserver_url": {"type": "string"},
            "contract_deployment": {"type": "string"},
            "rpc_url": {"type": "string"},
            "deposit_minimum": {"type": "number"},
            "deposit_amount": {"type": "number"},
            "sleep_rate": {"type": "number"},
            "bot_address": {"type": "string"},
            "private_key": {"type": "string"},
            "markets": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "levels_to_quote": {"type": "number"},
                        "price_offset": {"type": "number"},
                        "quantity_per_level": {"type": "number"},
                        "ref_px_deviation_to_replace_orders": {"type": "number"},
                        "max_position_size": {"type": "number"},
                        "trading_strategy": {"type": "string"},
                    },
                    "minProperties": 7,
                },
                "minItems": 1,
                "uniqueItems": True,
            },
            "strategies": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "minProperties": 10,
    }

    jsonschema.validate(config_json, mm_schema)

    asyncio.run(main(config_json))
