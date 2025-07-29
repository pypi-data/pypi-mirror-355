import json
import pytest
import pytest_asyncio
import websockets
import logging
from ddx.realtime_client import RealtimeClient
from ddx.realtime_client.models import (
    Feed,
    FeedWithParams,
    MarkPriceParams,
    OrderBookL2Params,
    OrderBookL3Params,
    OrderIdentifier,
    OrderUpdateParams,
    StrategyIdentifier,
    StrategyUpdateParams,
    TraderUpdateParams,
)


# For testing, we override the WS_URL to point to our local server.
# (Alternatively, use monkeypatch to override the WS_URL in the config module.)


# Define a simple fake WebSocket server.
async def fake_websocket_server(websocket):
    async for message in websocket:
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            await websocket.send('{"error": "bad json"}')
            continue
        # If the message contains a nonce and indicates a subscription, reply with an acknowledgement.
        if "nonce" in data and "feeds" in data:
            # Create an acknowledgement payload with the given nonce and no error.
            ack = {
                "action": data["action"],
                "nonce": data["nonce"],
                "result": {"error": None},
            }
            await websocket.send(json.dumps(ack))
        else:
            # Otherwise, echo the message.
            await websocket.send(message)


# Set up a pytest fixture to run our fake server on localhost on a free port.
@pytest_asyncio.fixture(loop_scope="module")
async def ws_server():
    async with websockets.serve(fake_websocket_server, "localhost", 8765) as server:
        yield server


# Use monkeypatch to override WS_URL so that the client connects to our local server.
@pytest.fixture
def override_ws_url(monkeypatch):
    monkeypatch.setattr(
        "ddx.realtime_client.realtime_client.WS_URL",
        "ws://localhost:8765",
    )


# Mark our test as async.
@pytest.mark.asyncio(loop_scope="module")
async def test_subscribe_acknowledgement(ws_server, override_ws_url):
    async with RealtimeClient() as client:
        # Use the public subscribe_feeds API to subscribe.
        await client.subscribe_feeds(
            [
                FeedWithParams(
                    feed=Feed.ORDER_BOOK_L2,
                    params=OrderBookL2Params(symbol="ETHP", aggregation=1),
                )
            ]
        )


@pytest.mark.asyncio(loop_scope="module")
async def test_receive_order_book_l2(ws_server, override_ws_url):
    async with RealtimeClient() as client:
        await client.subscribe_feeds(
            [
                FeedWithParams(
                    feed=Feed.ORDER_BOOK_L2,
                    params=OrderBookL2Params(symbol="ETHP", aggregation=1),
                )
            ]
        )

        simulated_msg = {
            "feed": "ORDER_BOOK_L2",
            "params": {"symbol": "ETHP", "aggregation": 0.1},
            "contents": {
                "messageType": "PARTIAL",
                "ordinal": 0,
                "data": [
                    {"symbol": "ETHP", "side": 0, "amount": "50.25", "price": "2000.0"},
                    {"symbol": "ETHP", "side": 1, "amount": "100.5", "price": "2000.5"},
                ],
            },
        }
        client._dispatch_message(simulated_msg)
        received = await anext(client.receive_order_book_l2())
        assert received.feed == "ORDER_BOOK_L2"
        order_book = client.order_book_l2
        assert "ETHP" in order_book
        order = order_book["ETHP"]
        # In a PARTIAL update, later orders overwrite earlier ones.
        assert order.amount == "100.5"
        assert order.price == "2000.5"


@pytest.mark.asyncio(loop_scope="module")
async def test_receive_order_book_l3(ws_server, override_ws_url):
    async with RealtimeClient() as client:
        await client.subscribe_feeds(
            [
                FeedWithParams(
                    feed=Feed.ORDER_BOOK_L3, params=OrderBookL3Params(symbol="ETHP")
                )
            ]
        )

        simulated_msg = {
            "feed": "ORDER_BOOK_L3",
            "params": {"symbol": "ETHP"},
            "contents": {
                "messageType": "PARTIAL",
                "ordinal": 0,
                "data": [
                    {
                        "orderHash": "0x92aaeac66831b00d0db66517debb3eac7370105d854420ed82",
                        "symbol": "ETHP",
                        "side": 0,
                        "originalAmount": "50",
                        "amount": "50",
                        "price": "2000",
                        "traderAddress": "0x00112233445566778899aabbccddeeff0011223344",
                        "strategyIdHash": "0x2576ebd1",
                        "bookOrdinal": 0,
                    },
                    {
                        "orderHash": "0x83bcdac12345b00d0eb66517debb3eac7370105d854420ed83",
                        "symbol": "ETHP",
                        "side": 1,
                        "originalAmount": "30",
                        "amount": "30",
                        "price": "2001",
                        "traderAddress": "0x00abcdef0123456789abcdef0123456789abcdef01",
                        "strategyIdHash": "0x2576ebd1",
                        "bookOrdinal": 1,
                    },
                ],
            },
        }
        client._dispatch_message(simulated_msg)
        received = await anext(client.receive_order_book_l3())
        assert received.feed == "ORDER_BOOK_L3"
        order_book = client.order_book_l3
        assert "0x92aaeac66831b00d0db66517debb3eac7370105d854420ed82" in order_book
        order = order_book["0x92aaeac66831b00d0db66517debb3eac7370105d854420ed82"]
        assert order.amount == "50"
        assert order.price == "2000"


@pytest.mark.asyncio(loop_scope="module")
async def test_receive_mark_price(ws_server, override_ws_url):
    async with RealtimeClient() as client:
        await client.subscribe_feeds(
            [
                FeedWithParams(
                    feed=Feed.MARK_PRICE, params=MarkPriceParams(symbols=["ETHP"])
                )
            ]
        )

        simulated_msg = {
            "feed": "MARK_PRICE",
            "params": {"symbols": ["ETHP"]},
            "contents": {
                "messageType": "PARTIAL",
                "ordinal": 0,
                "data": [
                    {
                        "epochId": 43,
                        "price": "1986.81",
                        "fundingRate": "0.000381",
                        "symbol": "ETHP",
                        "createdAt": "2023-10-01T12:00:30Z",
                    }
                ],
            },
        }
    client._dispatch_message(simulated_msg)
    received = await anext(client.receive_mark_price())
    assert received.feed == "MARK_PRICE"
    mark_prices = client.mark_prices
    assert "ETHP" in mark_prices
    entry = mark_prices["ETHP"]
    assert entry == "1986.81"
    funding_rates = client.funding_rates
    assert "ETHP" in funding_rates
    entry = funding_rates["ETHP"]
    assert entry == "0.000381"


@pytest.mark.asyncio(loop_scope="module")
async def test_receive_order_update(ws_server, override_ws_url):
    async with RealtimeClient() as client:
        await client.subscribe_feeds(
            [
                FeedWithParams(
                    feed=Feed.ORDER_UPDATE,
                    params=OrderUpdateParams(
                        order_identifiers=[
                            OrderIdentifier(
                                trader_address="0x00aabbccddeeff00112233445566778899aabbccdd",
                                symbol="ETHP",
                                strategy_id_hash="0x2576ebd1",
                            )
                        ]
                    ),
                )
            ]
        )

        simulated_msg = {
            "feed": "ORDER_UPDATE",
            "params": {
                "orderIdentifiers": [
                    {
                        "traderAddress": "0x00aabbccddeeff00112233445566778899aabbccdd",
                        "symbol": "ETHP",
                        "strategyIdHash": "0x2576ebd1",
                    }
                ]
            },
            "contents": {
                "messageType": "UPDATE",
                "ordinal": 0,
                "data": [
                    {
                        "epochId": 200,
                        "reason": 0,
                        "amount": "20",
                        "quoteAssetAmount": "2000",
                        "symbol": "ETHP",
                        "price": "100",
                        "orderMatchOrdinal": 10,
                        "ordinal": 0,
                        "lastExecutedAmount": "20",
                        "lastExecutedPrice": "100",
                        "cumulativeFilledAmount": "20",
                        "cumulativeQuoteAssetTransactedAmount": "2000",
                        "lastQuoteAssetTransactedAmount": "2000",
                        "makerRealizedPnl": "30",
                        "takerFeeDDX": "0.05",
                        "takerRealizedPnl": "50",
                        "makerOrderIntent": {
                            "epochId": 200,
                            "orderHash": "0xa1b2c3d4e5f67890abcdef01234567891234567890123456789",
                            "symbol": "ETHP",
                            "side": 0,
                            "amount": "20",
                            "price": "100",
                            "traderAddress": "0x00f1e2d3c4b5a6978899aabbccddeeff1122334455",
                            "strategyIdHash": "0x2576ebd1",
                            "orderType": 0,
                            "stopPrice": "0",
                            "nonce": "nonce-maker-1",
                            "signature": "0xfedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210",
                            "createdAt": "2023-10-01T11:59:50Z",
                        },
                        "takerOrderIntent": {
                            "epochId": 200,
                            "orderHash": "0xb1c2d3e4f5a67890abcdef0123456789234567890abcdef12",
                            "symbol": "ETHP",
                            "side": 1,
                            "amount": "20",
                            "price": "100",
                            "traderAddress": "0x00aabbccddeeff00112233445566778899aabbccdd",
                            "strategyIdHash": "0x2576ebd1",
                            "orderType": 0,
                            "stopPrice": "0",
                            "nonce": "nonce-taker-1",
                            "signature": "0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
                            "createdAt": "2023-10-01T11:59:55Z",
                        },
                        "createdAt": "2023-10-01T12:00:05Z",
                    },
                ],
            },
        }
    client._dispatch_message(simulated_msg)
    received = await anext(client.receive_order_update())
    assert received.feed == "ORDER_UPDATE"


@pytest.mark.asyncio(loop_scope="module")
async def test_receive_strategy_update(ws_server, override_ws_url):
    async with RealtimeClient() as client:
        await client.subscribe_feeds(
            [
                FeedWithParams(
                    feed=Feed.STRATEGY_UPDATE,
                    params=StrategyUpdateParams(
                        strategy_identifiers=[
                            StrategyIdentifier(
                                trader_address="0x00aabbccddeeff00112233445566778899aabbccdd",
                                strategy_id_hash="0x2576ebd1",
                            )
                        ]
                    ),
                )
            ]
        )

        simulated_msg = {
            "feed": "STRATEGY_UPDATE",
            "params": {
                "strategyIdentifiers": [
                    {
                        "traderAddress": "0x00aabbccddeeff00112233445566778899aabbccdd",
                        "strategyIdHash": "0x2576ebd1",
                    }
                ]
            },
            "contents": {
                "messageType": "UPDATE",
                "ordinal": 1,
                "data": [
                    {
                        "epochId": 300,
                        "reason": 0,
                        "traderAddress": "0x00a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9",
                        "strategyIdHash": "0x2576ebd1",
                        "collateralAddress": "0x00aabbccddeeff00112233445566778899aabbccdd",
                        "collateralSymbol": "USDC",
                        "amount": "1000",
                        "newAvailCollateral": "5000",
                        "blockNumber": 150000,
                        "createdAt": "2023-10-01T12:05:00Z",
                    },
                ],
            },
        }
    client._dispatch_message(simulated_msg)
    received = await anext(client.receive_strategy_update())
    assert received.feed == "STRATEGY_UPDATE"


@pytest.mark.asyncio(loop_scope="module")
async def test_receive_trader_update(ws_server, override_ws_url):
    async with RealtimeClient() as client:
        await client.subscribe_feeds(
            [
                FeedWithParams(
                    feed=Feed.TRADER_UPDATE,
                    params=TraderUpdateParams(
                        trader_addresses=[
                            "0x00aabbccddeeff00112233445566778899aabbccdd",
                        ]
                    ),
                )
            ]
        )

        simulated_msg = {
            "feed": "TRADER_UPDATE",
            "params": {
                "traderAddresses": ["0x00aabbccddeeff00112233445566778899aabbccdd"]
            },
            "contents": {
                "messageType": "UPDATE",
                "ordinal": 1,
                "data": [
                    {
                        "epochId": 500,
                        "reason": 0,
                        "traderAddress": "0x00aabbccddeeff00112233445566778899aabbccdd",
                        "amount": "150",
                        "newAvailDDXBalance": "1150",
                        "blockNumber": 123456,
                        "createdAt": "2023-10-01T12:15:00Z",
                    },
                ],
            },
        }
    client._dispatch_message(simulated_msg)
    received = await anext(client.receive_trader_update())
    assert received.feed == "TRADER_UPDATE"


@pytest.mark.asyncio(loop_scope="module")
async def test_unsubscribe_acknowledgement(ws_server, override_ws_url):
    async with RealtimeClient() as client:
        # Use the public unsubscribe_feeds API.
        await client.unsubscribe_feeds([Feed.ORDER_BOOK_L2])


@pytest.mark.asyncio(loop_scope="module")
async def test_custom_handler(ws_server, override_ws_url):
    async with RealtimeClient() as client:
        data = None

        # Define a custom handler for the ORDER_BOOK_L2 feed.
        def custom_handler(contents):
            logging.info(f"Custom handler received data: {contents}")
            nonlocal data
            data = contents

        # Subscribe to the ORDER_BOOK_L2 feed with the custom handler.
        await client.subscribe_feeds(
            [
                (
                    FeedWithParams(
                        feed=Feed.ORDER_BOOK_L2,
                        params=OrderBookL2Params(symbol="ETHP", aggregation=1),
                    ),
                    custom_handler,
                )
            ],
        )
        # Simulate receiving a message and check if the custom handler is called.
        simulated_msg = {
            "feed": "ORDER_BOOK_L2",
            "params": {"symbol": "ETHP", "aggregation": 0.1},
            "contents": {
                "messageType": "PARTIAL",
                "ordinal": 0,
                "data": [
                    {"symbol": "ETHP", "side": 0, "amount": "50.25", "price": "2000.0"},
                    {"symbol": "ETHP", "side": 1, "amount": "100.5", "price": "2000.5"},
                ],
            },
        }
        client._dispatch_message(simulated_msg)
        assert data is not None
