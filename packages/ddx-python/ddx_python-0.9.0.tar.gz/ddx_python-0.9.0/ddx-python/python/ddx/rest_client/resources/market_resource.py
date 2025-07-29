from typing import Optional, AsyncIterator, List, Dict

from ddx.rest_client.constants.endpoints import Market
from ddx.rest_client.resources.base_resource import BaseResource
from ddx.rest_client.models.market import (
    MarkPriceHistoryResponse,
    MarkPrice,
    FundingRateHistoryResponse,
    FundingRate,
    OrderBookL3Response,
    OrderUpdate,
    OrderUpdateHistoryResponse,
    Ticker,
    TickerResponse,
    OpenInterest,
    OpenInterestHistoryResponse,
    PriceCheckpoint,
    PriceCheckpointHistoryResponse,
    VolumeAggregation,
    OrderBook,
    OrderBookL2Response,
    FeeAggregationResponse,
    FeeAggregation,
    VolumeAggregationResponse,
    FundingRateComparisonAggregationResponse,
)


class MarketResource(BaseResource):
    """
    Market-related operations and data access.

    Provides access to market data, order books, mark prices, and other
    market-related information through the Exchange API endpoints.
    """

    async def get_mark_price_history_page(
        self,
        symbol: Optional[str] = None,
        limit: Optional[int] = None,
        epoch: Optional[int] = None,
        order: Optional[str] = None,
        offset: Optional[int] = None,
    ) -> MarkPriceHistoryResponse:
        """
        Get a single page of mark prices.

        Parameters
        ----------
        symbol : Optional[str]
            The symbol to get mark prices for
        limit : Optional[int]
            The number of rows to return
        epoch : Optional[int]
            The epoch boundary used when fetching the next timeseries page
        order : Optional[str]
            The ordering of the results ("asc" or "desc")
        offset : Optional[int]
            The offset of returned rows

        Returns
        -------
        MarkPriceHistoryResponse
            Single page of mark prices
        """

        # Build query parameters, excluding None values
        params = {
            "symbol": symbol,
            "limit": limit,
            "epoch": epoch,
            "order": order,
            "offset": offset,
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Make the request
        response = await self._http.get(
            self._build_url(Market.GET_MARK_PRICE_HISTORY), params=params
        )

        # Parse the response with Pydantic
        return MarkPriceHistoryResponse.model_validate(response)

    async def get_mark_price_history(
        self,
        symbol: Optional[str] = None,
        limit: Optional[int] = 100,
        order: Optional[str] = None,
    ) -> AsyncIterator[MarkPrice]:
        """
        Get all mark prices.

        Automatically handles pagination using offset.

        Parameters
        ----------
        symbol : Optional[str]
            The symbol to get mark prices for
        limit : Optional[int]
            The number of rows to return per page
        order : Optional[str]
            The ordering of the results ("asc" or "desc")

        Yields
        ------
        MarkPrice
            Mark price entries
        """
        offset = 0

        while True:
            response = await self.get_mark_price_history_page(
                symbol=symbol,
                limit=limit,
                order=order,
                offset=offset,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            offset += len(response.value)

    async def get_funding_rate_history_page(
        self,
        limit: Optional[int] = None,
        epoch: Optional[int] = None,
        tx_ordinal: Optional[int] = None,
        order: Optional[str] = None,
        symbol: Optional[str] = None,
        since: Optional[int] = None,
    ) -> FundingRateHistoryResponse:
        """
        Get a single page of funding rate history.

        Parameters
        ----------
        limit : Optional[int]
            Maximum number of results to return
        epoch : Optional[int]
            Filter by specific epoch
        tx_ordinal : Optional[int]
            Filter by transaction ordinal
        order : Optional[str]
            Sort order ("asc" or "desc")
        symbol : Optional[str]
            Filter by market symbol
        since : Optional[int]
            Filter by timestamp

        Returns
        -------
        FundingRateHistoryResponse
            Single page of funding rates with pagination metadata
        """
        params = {
            "limit": limit,
            "epoch": epoch,
            "txOrdinal": tx_ordinal,
            "order": order,
            "symbol": symbol,
            "since": since,
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Make the request
        response = await self._http.get(
            self._build_url(Market.GET_FUNDING_RATE_HISTORY), params=params
        )

        # Parse the response with Pydantic
        return FundingRateHistoryResponse.model_validate(response)

    async def get_funding_rate_history(
        self,
        limit: Optional[int] = None,
        order: Optional[str] = None,
        symbol: Optional[str] = None,
        since: Optional[int] = None,
    ) -> AsyncIterator[FundingRate]:
        """
        Get all funding rate history.

        Automatically handles pagination.

        Parameters
        ----------
        limit : Optional[int]
            Maximum number of results per page
        order : Optional[str]
            Sort order ("asc" or "desc")
        symbol : Optional[str]
            Filter by market symbol
        since : Optional[int]
            Filter by timestamp

        Yields
        ------
        FundingRateHistory
            Funding rate entries
        """
        epoch = None
        tx_ordinal = None

        while True:
            response = await self.get_funding_rate_history_page(
                limit=limit,
                epoch=epoch,
                tx_ordinal=tx_ordinal,
                order=order,
                symbol=symbol,
                since=since,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if not response.next_epoch:
                break

            epoch = response.next_epoch
            tx_ordinal = response.next_tx_ordinal

    async def get_order_book_l3(
        self,
        symbol: Optional[str] = None,
        trader: Optional[str] = None,
        strategy_id_hash: Optional[str] = None,
        depth: Optional[int] = None,
        side: Optional[int] = None,
    ) -> OrderBookL3Response:
        """
        Get current L3 order book.

        Parameters
        ----------
        symbol : Optional[str]
            The symbol to get the order book for
        trader : Optional[str]
            Filter by trader address with discriminant prefix
        strategy_id_hash : Optional[str]
            Filter by strategy ID hash
        depth : Optional[int]
            The best N bids and asks to return, where N = depth
        side : Optional[int]
            Filter by side (0: Bid, 1: Ask)

        Returns
        -------
        OrderBookL3Response
            Current L3 order book data
        """

        params = {
            "symbol": symbol,
            "trader": trader,
            "strategyIdHash": strategy_id_hash,
            "depth": depth,
            "side": side,
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Make the request
        response = await self._http.get(
            self._build_url(Market.GET_ORDER_BOOK_L3), params=params
        )

        # Parse the response with Pydantic
        return OrderBookL3Response.model_validate(response)

    async def get_order_update_history_page(
        self,
        trader: Optional[str] = None,
        strategy_id_hash: Optional[str] = None,
        limit: Optional[int] = None,
        epoch: Optional[int] = None,
        tx_ordinal: Optional[int] = None,
        ordinal: Optional[int] = None,
        order: Optional[str] = None,
        symbol: Optional[str] = None,
        order_hash: Optional[str] = None,
        reason: Optional[int] = None,
        since: Optional[int] = None,
    ) -> OrderUpdateHistoryResponse:
        """
        Get a single page of order updates (trades, liquidations, cancels).

        Parameters
        ----------
        trader : Optional[str]
            Filter by trader address with discriminant prefix
        strategy_id_hash : Optional[str]
            Filter by strategy ID hash
        limit : Optional[int]
            Maximum number of results to return
        epoch : Optional[int]
            Filter by specific epoch
        tx_ordinal : Optional[int]
            Filter by transaction ordinal
        ordinal : Optional[int]
            Filter by ordinal
        order : Optional[str]
            Sort order ("asc" or "desc")
        symbol : Optional[str]
            Filter by market symbol
        order_hash : Optional[str]
            Filter by order hash
        reason : Optional[int]
            Filter by reason (0: trade, 1: liquidation, 2: cancel)
        since : Optional[int]
            Filter by timestamp

        Returns
        -------
        OrderUpdateResponse
            Single page of order updates with pagination metadata
        """

        params = {
            "trader": trader,
            "strategyIdHash": strategy_id_hash,
            "limit": limit,
            "epoch": epoch,
            "txOrdinal": tx_ordinal,
            "ordinal": ordinal,
            "order": order,
            "symbol": symbol,
            "orderHash": order_hash,
            "reason": reason,
            "since": since,
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Make the request
        response = await self._http.get(
            self._build_url(Market.GET_ORDER_UPDATE_HISTORY), params=params
        )

        # Parse the response with Pydantic
        return OrderUpdateHistoryResponse.model_validate(response)

    async def get_order_update_history(
        self,
        trader: Optional[str] = None,
        strategy_id_hash: Optional[str] = None,
        limit: Optional[int] = 100,
        order: Optional[str] = None,
        symbol: Optional[str] = None,
        order_hash: Optional[str] = None,
        reason: Optional[int] = None,
        since: Optional[int] = None,
    ) -> AsyncIterator[OrderUpdate]:
        """
        Get all order updates (trades, liquidations, cancels).

        Automatically handles pagination.

        Parameters
        ----------
        trader : Optional[str]
            Filter by trader address with discriminant prefix
        strategy_id_hash : Optional[str]
            Filter by strategy ID hash
        limit : Optional[int]
            Maximum number of results per page
        order : Optional[str]
            Sort order ("asc" or "desc")
        symbol : Optional[str]
            Filter by market symbol
        order_hash : Optional[str]
            Filter by order hash
        reason : Optional[int]
            Filter by reason (0: trade, 1: liquidation, 2: cancel)
        since : Optional[int]
            Filter by timestamp

        Yields
        ------
        OrderUpdate
            Order update entries
        """

        epoch = None
        tx_ordinal = None
        ordinal = None

        while True:
            response = await self.get_order_update_history_page(
                trader=trader,
                strategy_id_hash=strategy_id_hash,
                limit=limit,
                epoch=epoch,
                tx_ordinal=tx_ordinal,
                ordinal=ordinal,
                order=order,
                symbol=symbol,
                order_hash=order_hash,
                reason=reason,
                since=since,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if not response.next_epoch:
                break

            epoch = response.next_epoch
            tx_ordinal = response.next_tx_ordinal
            ordinal = response.next_ordinal

    async def get_tickers(self, symbol: Optional[str] = None) -> List[Ticker]:
        """
        Get 24h OHLC/V and price-change data.

        Parameters
        ----------
        symbol : Optional[str]
            Filter by market symbol

        Returns
        -------
        List[Ticker]
            List of ticker data for markets
        """

        params = {}
        if symbol:
            params["symbol"] = symbol

        # Make the request
        response = await self._http.get(
            self._build_url(Market.GET_TICKERS), params=params
        )

        # Parse the response with Pydantic
        ticker_response = TickerResponse.model_validate(response)

        return ticker_response.value

    async def get_open_interest_history_page(
        self,
        limit: Optional[int] = None,
        order: Optional[str] = None,
        symbol: Optional[str] = None,
        interval: Optional[str] = None,
        since: Optional[int] = None,
    ) -> OpenInterestHistoryResponse:
        """
        Get a single page of open interest history.

        Parameters
        ----------
        limit : Optional[int]
            Maximum number of results to return
        order : Optional[str]
            Sort order ("asc" or "desc")
        symbol : Optional[str]
            Filter by market symbol
        interval : Optional[str]
            The interval for open interest history ("5m", "1h", "1d")
        since : Optional[int]
            Filter by timestamp

        Returns
        -------
        OpenInterestHistoryResponse
            Single page of open interest history
        """

        params = {
            "limit": limit,
            "order": order,
            "symbol": symbol,
            "interval": interval,
            "since": since,
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Make the request
        response = await self._http.get(
            self._build_url(Market.GET_OPEN_INTEREST_HISTORY), params=params
        )

        # Parse the response with Pydantic
        return OpenInterestHistoryResponse.model_validate(response)

    async def get_open_interest_history(
        self,
        limit: Optional[int] = 100,
        order: Optional[str] = None,
        symbol: Optional[str] = None,
        interval: Optional[str] = None,
        since: Optional[int] = None,
    ) -> AsyncIterator[OpenInterest]:
        """
        Get all open interest history.

        Automatically handles pagination.

        Parameters
        ----------
        limit : Optional[int]
            Maximum number of results per page
        order : Optional[str]
            Sort order ("asc" or "desc")
        symbol : Optional[str]
            Filter by market symbol
        interval : Optional[str]
            The interval for open interest history ("5m", "1h", "1d")
        since : Optional[int]
            Filter by timestamp

        Yields
        ------
        OpenInterest
            Open interest entries
        """

        offset = 0

        while True:
            response = await self.get_open_interest_history_page(
                limit=limit,
                order=order,
                symbol=symbol,
                interval=interval,
                since=since,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            # For this endpoint, we need to implement offset-based pagination
            # since the API doesn't provide next cursors
            offset += len(response.value)
            if len(response.value) < limit:
                break

    async def get_price_checkpoint_history_page(
        self,
        limit: Optional[int] = None,
        epoch: Optional[int] = None,
        tx_ordinal: Optional[int] = None,
        order: Optional[str] = None,
        symbol: Optional[str] = None,
        price_hash: Optional[str] = None,
    ) -> PriceCheckpointHistoryResponse:
        """
        Get a single page of price checkpoints.

        Parameters
        ----------
        limit : Optional[int]
            Maximum number of results to return
        epoch : Optional[int]
            Filter by specific epoch
        tx_ordinal : Optional[int]
            Filter by transaction ordinal
        order : Optional[str]
            Sort order ("asc" or "desc")
        symbol : Optional[str]
            Filter by market symbol
        price_hash : Optional[str]
            Filter by price hash

        Returns
        -------
        PriceCheckpointHistoryResponse
            Single page of price checkpoints with pagination metadata
        """

        params = {
            "limit": limit,
            "epoch": epoch,
            "txOrdinal": tx_ordinal,
            "order": order,
            "symbol": symbol,
            "priceHash": price_hash,
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Make the request
        response = await self._http.get(
            self._build_url(Market.GET_PRICE_CHECKPOINTS), params=params
        )

        # Parse the response with Pydantic
        return PriceCheckpointHistoryResponse.model_validate(response)

    async def get_price_checkpoint_history(
        self,
        limit: Optional[int] = 100,
        order: Optional[str] = None,
        symbol: Optional[str] = None,
        price_hash: Optional[str] = None,
    ) -> AsyncIterator[PriceCheckpoint]:
        """
        Get all price checkpoints.

        Automatically handles pagination.

        Parameters
        ----------
        limit : Optional[int]
            Maximum number of results per page
        order : Optional[str]
            Sort order ("asc" or "desc")
        symbol : Optional[str]
            Filter by market symbol
        price_hash : Optional[str]
            Filter by price hash

        Yields
        ------
        PriceCheckpoint
            Price checkpoint entries
        """

        epoch = None
        tx_ordinal = None
        ordinal = None

        while True:
            response = await self.get_price_checkpoint_history_page(
                limit=limit,
                epoch=epoch,
                tx_ordinal=tx_ordinal,
                order=order,
                symbol=symbol,
                price_hash=price_hash,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if not response.next_epoch:
                break

            epoch = response.next_epoch
            tx_ordinal = response.next_tx_ordinal
            ordinal = response.next_ordinal

    async def get_volume_aggregation_page(
        self,
        group: Optional[str] = "symbol",
        symbol: Optional[str] = None,
        aggregation_period: Optional[str] = "day",
        lookback_count: Optional[int] = None,
        lookback_timestamp: Optional[int] = None,
    ) -> VolumeAggregationResponse:
        """
        Get a single page of volume data aggregated over time periods.

        Parameters
        ----------
        group : Optional[str]
            The grouping for the aggregation ("symbol")
        symbol : Optional[str]
            Filter by market symbol
        aggregation_period : Optional[str]
            The period for aggregation ("week", "day", "hour", "minute")
        lookback_count : Optional[int]
            The number of periods to look back from present
        lookback_timestamp : Optional[int]
            The timestamp to begin the lookback from

        Returns
        -------
        VolumeAggregationHistoryResponse
            Single page of volume aggregation data with pagination metadata
        """

        # Implementation remains the same
        params = {
            "group": group,
            "symbol": symbol,
            "aggregationPeriod": aggregation_period,
            "lookbackCount": lookback_count,
            "lookbackTimestamp": lookback_timestamp,
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Make the request
        response = await self._http.get(
            self._build_url(Market.GET_VOLUME_AGGREGATION), params=params
        )

        # Parse the response with Pydantic
        return VolumeAggregationResponse.model_validate(response)

    async def get_volume_aggregation(
        self,
        group: Optional[str] = "symbol",
        symbol: Optional[str] = None,
        aggregation_period: Optional[str] = "day",
        lookback_count: Optional[int] = None,
    ) -> AsyncIterator[VolumeAggregation]:
        """
        Get all volume data aggregated over time periods.

        Automatically handles pagination.

        Parameters
        ----------
        group : Optional[str]
            The grouping for the aggregation ("symbol")
        symbol : Optional[str]
            Filter by market symbol
        aggregation_period : Optional[str]
            The period for aggregation ("week", "day", "hour", "minute")
        lookback_count : Optional[int]
            The number of periods to look back from present

        Yields
        ------
        VolumeAggregation
            Volume aggregation entries
        """

        lookback_timestamp = None

        while True:
            response = await self.get_volume_aggregation_page(
                group=group,
                symbol=symbol,
                aggregation_period=aggregation_period,
                lookback_count=lookback_count,
                lookback_timestamp=lookback_timestamp,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if not response.next_lookback_timestamp:
                break

            lookback_timestamp = response.next_lookback_timestamp

    async def get_funding_rate_comparison_aggregation(
        self,
        symbol: Optional[str] = None,
    ) -> FundingRateComparisonAggregationResponse:
        """
        Get funding rate comparison data between DerivaDEX and major exchanges.

        Parameters
        ----------
        symbol : Optional[str]
            Filter by market symbol

        Returns
        -------
        FundingRateComparisonAggregationResponse
            Funding rate comparison data
        """

        params = {
            "symbol": symbol,
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Make the request
        response = await self._http.get(
            self._build_url(Market.GET_FUNDING_RATE_COMPARISON_AGGREGATION),
            params=params,
        )

        # Parse the response with Pydantic
        return FundingRateComparisonAggregationResponse.model_validate(response)

    async def get_fee_aggregation_page(
        self,
        group: Optional[str] = None,
        symbol: Optional[str] = None,
        fee_symbol: Optional[str] = None,
        aggregation_period: Optional[str] = "day",
        lookback_count: Optional[int] = None,
        lookback_timestamp: Optional[int] = None,
    ) -> FeeAggregationResponse:
        """
        Get a single page of fees data aggregated over time periods.

        Parameters
        ----------
        group : Optional[str]
            The grouping for the aggregation ("symbol" or "feeSymbol")
        symbol : Optional[str]
            Filter by market symbol
        fee_symbol : Optional[str]
            Filter by fee symbol ("USDC" or "DDX")
        aggregation_period : Optional[str]
            The period for aggregation ("week", "day", "hour", "minute")
        lookback_count : Optional[int]
            The number of periods to look back from present
        lookback_timestamp : Optional[int]
            The timestamp to begin the lookback from

        Returns
        -------
        FeeAggregationResponse
            Single page of fees aggregation data with pagination metadata
        """

        params = {
            "group": group,
            "symbol": symbol,
            "feeSymbol": fee_symbol,
            "aggregationPeriod": aggregation_period,
            "lookbackCount": lookback_count,
            "lookbackTimestamp": lookback_timestamp,
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Make the request
        response = await self._http.get(
            self._build_url(Market.GET_FEE_AGGREGATION), params=params
        )

        # Parse the response with Pydantic
        return FeeAggregationResponse.model_validate(response)

    async def get_fee_aggregation(
        self,
        group: Optional[str] = None,
        symbol: Optional[str] = None,
        fee_symbol: Optional[str] = None,
        aggregation_period: Optional[str] = "day",
        lookback_count: Optional[int] = None,
    ) -> AsyncIterator[FeeAggregation]:
        """
        Get all fees data aggregated over time periods.

        Automatically handles pagination.

        Parameters
        ----------
        group : Optional[str]
            The grouping for the aggregation ("symbol" or "feeSymbol")
        symbol : Optional[str]
            Filter by market symbol
        fee_symbol : Optional[str]
            Filter by fee symbol ("USDC" or "DDX")
        aggregation_period : Optional[str]
            The period for aggregation ("week", "day", "hour", "minute")
        lookback_count : Optional[int]
            The number of periods to look back from present

        Yields
        ------
        FeeAggregation
            Fee aggregation entries
        """
        lookback_timestamp = None

        while True:
            response = await self.get_fee_aggregation_page(
                group=group,
                symbol=symbol,
                fee_symbol=fee_symbol,
                aggregation_period=aggregation_period,
                lookback_count=lookback_count,
                lookback_timestamp=lookback_timestamp,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if not response.next_lookback_timestamp:
                break

            lookback_timestamp = response.next_lookback_timestamp

    async def get_order_book_l2(
        self,
        symbol: Optional[str] = None,
        depth: Optional[int] = None,
        side: Optional[int] = None,
        price_aggregation: Optional[float] = None,
    ) -> Dict[str, OrderBook]:
        """
        Get current L2 aggregated order book.

        Parameters
        ----------
        symbol : Optional[str]
            The symbol to get the order book for
        depth : Optional[int]
            The best N bids and asks to return, where N = depth
        side : Optional[int]
            Filter by side (0: Bid, 1: Ask)
        price_aggregation : Optional[float]
            The price aggregation to use (e.g., 0.1, 1, 10)

        Returns
        -------
        Dict[str, OrderBook]
            Dictionary mapping symbols to their respective order books
        """

        params = {
            "symbol": symbol,
            "depth": depth,
            "side": side,
            "priceAggregation": price_aggregation,
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Make the request
        response = await self._http.get(
            self._build_url(Market.GET_ORDER_BOOK_L2), params=params
        )

        # Parse the response with Pydantic
        parsed_response = OrderBookL2Response.model_validate(response)

        # Convert to OrderBook objects
        return OrderBook.from_response(parsed_response, symbol)
