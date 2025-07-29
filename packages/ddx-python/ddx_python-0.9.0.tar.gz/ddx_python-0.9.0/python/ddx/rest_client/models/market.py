from datetime import datetime
from enum import IntEnum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, ConfigDict, field_validator
from pydantic.alias_generators import to_camel
from dateutil.parser import parse
from dataclasses import dataclass
from itertools import groupby
from operator import attrgetter

from ddx._rust.decimal import Decimal


class MarkPrice(BaseModel):
    """Mark price data model."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    funding_rate: float
    epoch_id: int
    request_index: int
    symbol: str
    price: float
    created_at: datetime

    @field_validator("created_at", mode="before")
    @classmethod
    def parse_datetime(cls, value):
        if isinstance(value, str):
            return parse(value)
        return value


class MarkPriceHistoryResponse(BaseModel):
    """Response model for mark price history endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    value: List[MarkPrice]
    success: bool
    timestamp: int


class FundingRate(BaseModel):
    """Funding rate history data model."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    epoch_id: int
    tx_ordinal: int
    symbol: str
    funding_rate: str
    created_at: datetime

    @field_validator("created_at", mode="before")
    @classmethod
    def parse_datetime(cls, value):
        if isinstance(value, str):
            return parse(value)
        return value


class FundingRateHistoryResponse(BaseModel):
    """Response model for funding rate history endpoint with cursor pagination."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    value: List[FundingRate]
    next_epoch: Optional[int] = None
    next_tx_ordinal: Optional[int] = None
    next_ordinal: Optional[int] = None
    success: bool
    timestamp: int


class OrderBookL3Item(BaseModel):
    """L3 order book item model."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    book_ordinal: int
    order_hash: str
    symbol: str
    side: int  # 0: Bid, 1: Ask
    original_amount: str
    amount: str
    price: str
    trader_address: str
    strategy_id_hash: str


class OrderBookL3Response(BaseModel):
    """Response model for L3 order book endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    value: List[OrderBookL3Item]
    success: bool
    timestamp: int


class OrderIntent(BaseModel):
    """Order intent model for maker and taker orders."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    epoch_id: int
    order_hash: str
    symbol: str
    side: int  # 0: Bid, 1: Ask
    amount: str
    price: str
    trader_address: str
    strategy_id_hash: str
    order_type: int  # 0: Limit, 1: Market, 2: Stop, 3: LimitPostOnly
    stop_price: str
    nonce: str
    signature: str
    created_at: datetime

    @field_validator("created_at", mode="before")
    @classmethod
    def parse_datetime(cls, value):
        if isinstance(value, str):
            return parse(value)
        return value


class OrderUpdate(BaseModel):
    """Order update model."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    epoch_id: int
    tx_ordinal: int
    ordinal: int
    order_rejection: Optional[int] = None
    cancel_rejection: Optional[int] = None
    reason: int  # 0: trade, 1: liquidation, 2: cancel
    amount: Optional[str] = None
    quote_asset_amount: Optional[str] = None
    symbol: str
    price: Optional[str] = None
    maker_fee_collateral: Optional[str] = None
    maker_fee_ddx: Optional[str] = None
    maker_realized_pnl: Optional[str] = None
    taker_order_intent: Optional[OrderIntent] = None
    taker_fee_collateral: Optional[str] = None
    taker_fee_ddx: Optional[str] = None
    taker_realized_pnl: Optional[str] = None
    liquidated_trader_address: Optional[str] = None
    liquidated_strategy_id_hash: Optional[str] = None
    maker_order_intent: OrderIntent
    created_at: datetime

    @field_validator("created_at", mode="before")
    @classmethod
    def parse_datetime(cls, value):
        if isinstance(value, str):
            return parse(value)
        return value


class OrderUpdateHistoryResponse(BaseModel):
    """Response model for order update history endpoint with cursor pagination."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    value: List[OrderUpdate]
    next_epoch: Optional[int] = None
    next_tx_ordinal: Optional[int] = None
    next_ordinal: Optional[int] = None
    success: bool
    timestamp: int


class Ticker(BaseModel):
    """Ticker data model for 24h OHLC/V and price-change data."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str
    high: Optional[str] = None
    low: Optional[str] = None
    volume_weighted_average_price: Optional[str] = None
    open: Optional[str] = None
    close: Optional[str] = None
    previous_close: Optional[str] = None
    change: Optional[str] = None
    percentage: Optional[str] = None
    base_volume: Optional[str] = None
    notional_volume: Optional[str] = None


class TickerResponse(BaseModel):
    """Response model for tickers endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    value: List[Ticker]
    success: bool
    timestamp: int


class OpenInterest(BaseModel):
    """Open interest data model."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str
    amount: str
    created_at: datetime

    @field_validator("created_at", mode="before")
    @classmethod
    def parse_datetime(cls, value):
        if isinstance(value, str):
            return parse(value)
        return value


class OpenInterestHistoryResponse(BaseModel):
    """Response model for open interest history endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    value: List[OpenInterest]
    success: bool
    timestamp: int


class PriceCheckpoint(BaseModel):
    """Price checkpoint model."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    epoch_id: str
    tx_ordinal: str
    index_price_hash: str
    symbol: str
    index_price: str
    mark_price: str
    time: str
    ema: Optional[str] = None
    price_ordinal: str
    created_at: datetime

    @field_validator("created_at", mode="before")
    @classmethod
    def parse_datetime(cls, value):
        if isinstance(value, str):
            return parse(value)
        return value


class PriceCheckpointHistoryResponse(BaseModel):
    """Response model for price checkpoint history endpoint with cursor pagination."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    value: List[PriceCheckpoint]
    next_epoch: Optional[int] = None
    next_tx_ordinal: Optional[int] = None
    next_ordinal: Optional[int] = None
    success: bool
    timestamp: int


class MarketData(BaseModel):
    """Market data model."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    market: str
    volume: str
    amount: Optional[str] = None
    price: str
    funding_rate: str
    open_interest: str


class MarketsResponse(BaseModel):
    """Response model for markets endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    value: List[MarketData]
    success: bool
    timestamp: int


class VolumeAggregation(BaseModel):
    """Volume aggregation data model."""

    model_config = ConfigDict(populate_by_name=True)

    timestamp: int
    # Dynamic fields will be handled with extra='allow'
    # Fields like volume_notional_overall will be accessible

    # Add method to get volume by symbol
    def get_volume(self, symbol: Optional[str] = None) -> Optional[str]:
        """Get volume for a specific symbol or overall volume."""
        if symbol:
            return getattr(self, f"volume_notional_{symbol.lower()}", None)
        return getattr(self, "volume_notional_overall", None)


class VolumeAggregationResponse(BaseModel):
    """Response model for volume aggregation endpoint."""

    model_config = ConfigDict(
        populate_by_name=True, alias_generator=to_camel, extra="allow"
    )

    value: List[VolumeAggregation]
    next_lookback_timestamp: Optional[int] = None
    success: bool
    timestamp: int


class FundingRateComparisonAggregation(BaseModel):
    """Funding rate comparison data model."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str
    derivadex_funding_rate: str
    binance_funding_rate: str
    derivadex_binance_arbitrage: str
    bybit_funding_rate: str
    derivadex_bybit_arbitrage: str


class FundingRateComparisonAggregationResponse(BaseModel):
    """Response model for funding rate comparison endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    value: List[FundingRateComparisonAggregation]
    success: bool
    timestamp: int


class FeeAggregation(BaseModel):
    """Fees aggregation data model."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    timestamp: int
    # Dynamic fields will be handled with extra='allow'
    # Fields like fees_DDX and fees_USDC will be accessible

    # Add method to get fees by symbol
    def get_fees(self, fee_symbol: Optional[str] = None) -> Optional[str]:
        """Get fees for a specific fee symbol."""
        if fee_symbol:
            return getattr(self, f"fees_{fee_symbol}", None)
        return None


class FeeAggregationResponse(BaseModel):
    """Response model for fees aggregation endpoint."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    value: List[FeeAggregation]
    next_lookback_timestamp: Optional[int] = None
    success: bool
    timestamp: int


class OrderSide(IntEnum):
    """Order side enum."""

    BID = 0
    ASK = 1


class OrderBookL2Item(BaseModel):
    """L2 order book item model."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str
    amount: str
    price: str
    side: int  # 0: Bid, 1: Ask


class OrderBookL2Response(BaseModel):
    """Response model for L2 order book endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    value: List[OrderBookL2Item]
    success: bool
    timestamp: int


@dataclass
class OrderBook:
    """
    Complete order book for a single market.

    Attributes
    ----------
    symbol : str
        The symbol of the market
    bids : List[OrderBookL2Item]
        List of bid orders, sorted by price (descending)
    asks : List[OrderBookL2Item]
        List of ask orders, sorted by price (ascending)
    timestamp : int
        Timestamp of the order book snapshot
    """

    symbol: str
    bids: List[OrderBookL2Item]
    asks: List[OrderBookL2Item]
    timestamp: int

    @classmethod
    def from_order_book_l2_items(
        cls, symbol: str, order_book_l2_items: List[OrderBookL2Item], timestamp: int
    ) -> "OrderBook":
        """
        Create instance from a list of entries for a single symbol.

        Parameters
        ----------
        symbol : str
            The market symbol
        order_book_l2_items : List[OrderBookL2Item]
            List of order book entries for this symbol
        timestamp : int
            Timestamp of the order book snapshot

        Returns
        -------
        OrderBook
            Initialized instance
        """
        # Filter and sort bids (descending)
        bids = [e for e in order_book_l2_items if e.side == OrderSide.BID]
        bids.sort(key=lambda x: Decimal(x.price), reverse=True)

        # Filter and sort asks (ascending)
        asks = [e for e in order_book_l2_items if e.side == OrderSide.ASK]
        asks.sort(key=lambda x: Decimal(x.price))

        return cls(symbol=symbol, bids=bids, asks=asks, timestamp=timestamp)

    @classmethod
    def from_response(
        cls, response: OrderBookL2Response, symbol: Optional[str] = None
    ) -> Dict[str, "OrderBook"]:
        """
        Create OrderBook instance(s) from response data.

        Parameters
        ----------
        response : OrderBookL2Response
            Parsed response from the API
        symbol : Optional[str]
            If provided, only return order book for this symbol

        Returns
        -------
        Dict[str, OrderBook]
            Dictionary mapping symbols to their respective order books
        """
        # Group entries by symbol
        grouped = groupby(
            sorted(response.value, key=attrgetter("symbol")), key=attrgetter("symbol")
        )

        # Create order books for each symbol
        order_books = {
            sym: cls.from_order_book_l2_items(sym, list(entries), response.timestamp)
            for sym, entries in grouped
        }

        # Filter to specific symbol if requested
        if symbol:
            return {symbol: order_books[symbol]} if symbol in order_books else {}

        return order_books
