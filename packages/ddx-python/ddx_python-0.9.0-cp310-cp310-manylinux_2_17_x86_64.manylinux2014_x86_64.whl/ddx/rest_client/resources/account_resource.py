from typing import Optional, AsyncIterator

from ddx.rest_client.constants.endpoints import Account
from ddx.rest_client.resources.base_resource import BaseResource
from ddx.rest_client.models.account import (
    TraderUpdate,
    TraderUpdateHistoryResponse,
    StrategyUpdateHistoryResponse,
    StrategyUpdate,
    TraderProfileResponse,
    StrategyFeeHistoryResponse,
    StrategyFee,
    StrategyResponse,
    StrategyMetricsResponse,
    PositionsResponse,
    StrategyBalanceChangeAggregationResponse,
    StrategyFundingRatePaymentAggregationResponse,
    StrategyRealizedPnlAggregationResponse,
    TradeMiningRewardAggregationResponse,
    TopTraderAggregationResponse,
    TopTraderAggregation,
)


class AccountResource(BaseResource):
    """
    Account-related operations and data access.

    Provides access to trader data, balances, and other
    account-related information through the API endpoints.
    """

    async def get_trader_update_history_page(
        self,
        trader: Optional[str] = None,
        reason: Optional[int] = None,
        limit: Optional[int] = None,
        epoch: Optional[int] = None,
        tx_ordinal: Optional[int] = None,
        ordinal: Optional[int] = None,
        order: Optional[str] = None,
    ) -> TraderUpdateHistoryResponse:
        """
        Get a single page of trader DDX balance and profile updates.

        Parameters
        ----------
        trader : Optional[str]
            The trader address with discriminant prefix
        reason : Optional[int]
            The type of trader update (0: Deposit, 1: WithdrawDDX, etc.)
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

        Returns
        -------
        TraderUpdateHistoryResponse
            Single page of trader updates with pagination metadata
        """

        params = {
            "trader": trader,
            "reason": reason,
            "limit": limit,
            "epoch": epoch,
            "txOrdinal": tx_ordinal,
            "ordinal": ordinal,
            "order": order,
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Make the request
        response = await self._http.get(
            self._build_url(Account.GET_TRADER_UPDATE_HISTORY), params=params
        )

        # Parse the response with Pydantic
        return TraderUpdateHistoryResponse.model_validate(response)

    async def get_trader_update_history(
        self,
        trader: Optional[str] = None,
        reason: Optional[int] = None,
        limit: Optional[int] = 100,
        order: Optional[str] = None,
    ) -> AsyncIterator[TraderUpdate]:
        """
        Get all trader DDX balance and profile updates.

        Automatically handles pagination.

        Parameters
        ----------
        trader : Optional[str]
            The trader address with discriminant prefix
        reason : Optional[int]
            The type of trader update (0: Deposit, 1: WithdrawDDX, etc.)
        limit : Optional[int]
            Maximum number of results per page
        order : Optional[str]
            Sort order ("asc" or "desc")

        Yields
        ------
        TraderUpdate
            Trader update entries
        """

        epoch = None
        tx_ordinal = None
        ordinal = None

        while True:
            response = await self.get_trader_update_history_page(
                trader=trader,
                reason=reason,
                limit=limit,
                epoch=epoch,
                tx_ordinal=tx_ordinal,
                ordinal=ordinal,
                order=order,
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

    async def get_strategy_update_history_page(
        self,
        trader: Optional[str] = None,
        strategy_id_hash: Optional[str] = None,
        reason: Optional[int] = None,
        limit: Optional[int] = None,
        epoch: Optional[int] = None,
        tx_ordinal: Optional[int] = None,
        ordinal: Optional[int] = None,
        order: Optional[str] = None,
    ) -> StrategyUpdateHistoryResponse:
        """
        Get a single page of strategy updates.

        Parameters
        ----------
        trader : Optional[str]
            The trader address with discriminant prefix
        strategy_id_hash : Optional[str]
            The strategy ID hash
        reason : Optional[int]
            The type of strategy update (0: Deposit, 1: Withdraw, etc.)
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

        Returns
        -------
        StrategyUpdateHistoryResponse
            Single page of strategy updates with pagination metadata
        """

        params = {
            "trader": trader,
            "strategyIdHash": strategy_id_hash,
            "reason": reason,
            "limit": limit,
            "epoch": epoch,
            "txOrdinal": tx_ordinal,
            "ordinal": ordinal,
            "order": order,
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Make the request
        response = await self._http.get(
            self._build_url(Account.GET_STRATEGY_UPDATE_HISTORY), params=params
        )

        # Parse the response with Pydantic
        return StrategyUpdateHistoryResponse.model_validate(response)

    async def get_strategy_update_history(
        self,
        trader: Optional[str] = None,
        strategy_id_hash: Optional[str] = None,
        reason: Optional[int] = None,
        limit: Optional[int] = 100,
        order: Optional[str] = None,
    ) -> AsyncIterator[StrategyUpdate]:
        """
        Get all strategy updates.

        Automatically handles pagination.

        Parameters
        ----------
        trader : Optional[str]
            The trader address with discriminant prefix
        strategy_id_hash : Optional[str]
            The strategy ID hash
        reason : Optional[int]
            The type of strategy update (0: Deposit, 1: Withdraw, etc.)
        limit : Optional[int]
            Maximum number of results per page
        order : Optional[str]
            Sort order ("asc" or "desc")

        Yields
        ------
        StrategyUpdate
            Strategy update entries
        """
        epoch = None
        tx_ordinal = None
        ordinal = None

        while True:
            response = await self.get_strategy_update_history_page(
                trader=trader,
                strategy_id_hash=strategy_id_hash,
                reason=reason,
                limit=limit,
                epoch=epoch,
                tx_ordinal=tx_ordinal,
                ordinal=ordinal,
                order=order,
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

    async def get_trader_profile(self, trader: str) -> TraderProfileResponse:
        """
        Get current trader DDX balance and profile.

        Parameters
        ----------
        trader : str
            The trader address with discriminant prefix

        Returns
        -------
        TraderProfileResponse
            Current trader profile data
        """

        # Make the request
        response = await self._http.get(
            self._build_url(Account.GET_TRADER_PROFILE, trader=trader)
        )

        # Parse the response with Pydantic
        return TraderProfileResponse.model_validate(response)

    async def get_strategy_fee_history_page(
        self,
        trader: str,
        strategy_id: str,
        limit: Optional[int] = None,
        epoch: Optional[int] = None,
        tx_ordinal: Optional[int] = None,
        ordinal: Optional[int] = None,
        symbol: Optional[str] = None,
        order: Optional[str] = None,
    ) -> StrategyFeeHistoryResponse:
        """
        Get a single page of maker/taker fee aggregates for a strategy.

        Parameters
        ----------
        trader : str
            The trader address
        strategy_id : str
            The strategy ID
        limit : Optional[int]
            Maximum number of results to return
        epoch : Optional[int]
            Filter by specific epoch
        tx_ordinal : Optional[int]
            Filter by transaction ordinal
        ordinal : Optional[int]
            Filter by ordinal
        symbol : Optional[str]
            Filter by market symbol
        order : Optional[str]
            Sort order ("asc" or "desc")

        Returns
        -------
        StrategyFeeHistoryResponse
            Single page of strategy fees with pagination metadata
        """

        params = {
            "limit": limit,
            "epoch": epoch,
            "txOrdinal": tx_ordinal,
            "ordinal": ordinal,
            "symbol": symbol,
            "order": order,
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Make the request
        response = await self._http.get(
            self._build_url(
                Account.GET_STRATEGY_FEE_HISTORY, trader=trader, strategyId=strategy_id
            ),
            params=params,
        )

        # Parse the response with Pydantic
        return StrategyFeeHistoryResponse.model_validate(response)

    async def get_strategy_fee_history(
        self,
        trader: str,
        strategy_id: str,
        limit: Optional[int] = 100,
        symbol: Optional[str] = None,
        order: Optional[str] = None,
    ) -> AsyncIterator[StrategyFee]:
        """
        Get all maker/taker fee aggregates for a strategy.

        Automatically handles pagination.

        Parameters
        ----------
        trader : str
            The trader address
        strategy_id : str
            The strategy ID
        limit : Optional[int]
            Maximum number of results per page
        symbol : Optional[str]
            Filter by market symbol
        order : Optional[str]
            Sort order ("asc" or "desc")

        Yields
        ------
        StrategyFee
            Strategy fee entries
        """
        epoch = None
        tx_ordinal = None
        ordinal = None

        while True:
            response = await self.get_strategy_fee_history_page(
                trader=trader,
                strategy_id=strategy_id,
                limit=limit,
                epoch=epoch,
                tx_ordinal=tx_ordinal,
                ordinal=ordinal,
                symbol=symbol,
                order=order,
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

    async def get_strategy(
        self,
        trader: str,
        strategy_id: str,
    ) -> StrategyResponse:
        """
        Get current state of trader's strategy.

        Parameters
        ----------
        trader : str
            The trader address
        strategy_id : str
            The strategy ID

        Returns
        -------
        StrategyResponse
            Current state of the trader's strategy
        """

        # Make the request
        response = await self._http.get(
            self._build_url(Account.GET_STRATEGY, trader=trader, strategyId=strategy_id)
        )

        # Parse the response with Pydantic
        return StrategyResponse.model_validate(response)

    async def get_strategy_metrics(
        self,
        trader: str,
        strategy_id: str,
    ) -> StrategyMetricsResponse:
        """
        Get KPIs and risk metrics for a strategy.

        Parameters
        ----------
        trader : str
            The trader address
        strategy_id : str
            The strategy ID

        Returns
        -------
        StrategyMetricsResponse
            Strategy metrics including margin fraction, maintenance margin ratio,
            leverage, strategy margin, and strategy value
        """

        # Make the request
        response = await self._http.get(
            self._build_url(
                Account.GET_STRATEGY_METRICS, trader=trader, strategyId=strategy_id
            )
        )

        # Parse the response with Pydantic
        return StrategyMetricsResponse.model_validate(response)

    async def get_positions(
        self,
        trader: str,
        strategy_id: str,
        symbol: Optional[str] = None,
    ) -> PositionsResponse:
        """
        Get current positions for a strategy.

        Parameters
        ----------
        trader : str
            The trader address
        strategy_id : str
            The strategy ID
        symbol : Optional[str]
            Filter by market symbol

        Returns
        -------
        PositionsResponse
            Current positions for the strategy
        """

        params = {
            "symbol": symbol,
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._http.get(
            self._build_url(
                Account.GET_POSITIONS, trader=trader, strategyId=strategy_id
            ),
            params=params,
        )

        # Parse the response with Pydantic
        return PositionsResponse.model_validate(response)

    async def get_strategy_balance_change_aggregation(
        self,
        trader: str,
        strategy_id: str,
        aggregation_period: Optional[str] = "day",
        lookback_count: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> StrategyBalanceChangeAggregationResponse:
        """
        Get the change of trader's balance for a specific strategy over time.

        Parameters
        ----------
        trader : str
            The trader address
        strategy_id : str
            The strategy ID
        aggregation_period : Optional[str]
            The period for aggregation ("week", "day", "hour", "minute")
        lookback_count : Optional[int]
            The number of periods to look back from present
        limit : Optional[int]
            Maximum number of results to return

        Returns
        -------
        StrategyBalanceChangeAggregationResponse
            Strategy balance change data
        """

        params = {
            "aggregationPeriod": aggregation_period,
            "lookbackCount": lookback_count,
            "limit": limit,
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Make the request
        response = await self._http.get(
            self._build_url(
                Account.GET_STRATEGY_BALANCE_CHANGE_AGGREGATION,
                trader=trader,
                strategyId=strategy_id,
            ),
            params=params,
        )

        # Parse the response with Pydantic
        return StrategyBalanceChangeAggregationResponse.model_validate(response)

    async def get_strategy_funding_rate_payment_aggregation(
        self,
        trader: str,
        strategy_id: str,
        aggregation_period: Optional[str] = None,
        lookback_count: Optional[int] = None,
    ) -> StrategyFundingRatePaymentAggregationResponse:
        """
        Get funding rate payments for a specific strategy.

        Parameters
        ----------
        trader : str
            The trader address
        strategy_id : str
            The strategy ID
        aggregation_period : Optional[str]
            The period for aggregation ("week", "day", "hour", "minute")
        lookback_count : Optional[int]
            The number of periods to look back from present

        Returns
        -------
        StrategyFundingRatePaymentAggregationResponse
            Funding rate payments data
        """

        params = {
            "aggregationPeriod": aggregation_period,
            "lookbackCount": lookback_count,
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Make the request
        response = await self._http.get(
            self._build_url(
                Account.GET_STRATEGY_FUNDING_RATE_PAYMENT_AGGREGATION,
                trader=trader,
                strategyId=strategy_id,
            ),
            params=params,
        )

        # Parse the response with Pydantic
        return StrategyFundingRatePaymentAggregationResponse.model_validate(response)

    async def get_strategy_realized_pnl_aggregation(
        self,
        trader: str,
        strategy_id: str,
        aggregation_period: Optional[str] = "day",
        lookback_count: Optional[int] = None,
    ) -> StrategyRealizedPnlAggregationResponse:
        """
        Get the change of trader's realized PNL per time period.

        Parameters
        ----------
        trader : str
            The trader address
        strategy_id : str
            The strategy ID
        aggregation_period : Optional[str]
            The period for aggregation ("week", "day", "hour", "minute")
        lookback_count : Optional[int]
            The number of periods to look back from present

        Returns
        -------
        StrategyRealizedPnlAggregationResponse
            Realized PNL aggregation data
        """

        params = {
            "aggregationPeriod": aggregation_period,
            "lookbackCount": lookback_count,
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Make the request
        response = await self._http.get(
            self._build_url(
                Account.GET_STRATEGY_REALIZED_PNL_AGGREGATION,
                trader=trader,
                strategyId=strategy_id,
            ),
            params=params,
        )

        # Parse the response with Pydantic
        return StrategyRealizedPnlAggregationResponse.model_validate(response)

    async def get_trade_mining_rewards(
        self,
        trader: str,
        aggregation_period: Optional[str] = "day",
        lookback_count: Optional[int] = None,
    ) -> TradeMiningRewardAggregationResponse:
        """
        Get aggregation of a trader's trade mining rewards.

        Parameters
        ----------
        trader : str
            The trader address
        aggregation_period : Optional[str]
            The period for aggregation ("week", "day", "hour", "minute")
        lookback_count : Optional[int]
            The number of periods to look back from present

        Returns
        -------
        TradeMiningRewardResponse
            Trade mining rewards aggregation data
        """

        params = {
            "aggregationPeriod": aggregation_period,
            "lookbackCount": lookback_count,
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._http.get(
            self._build_url(Account.GET_TRADE_MINING_REWARD_AGGREGATION, trader=trader),
            params=params,
        )

        # Parse the response with Pydantic
        return TradeMiningRewardAggregationResponse.model_validate(response)

    async def get_top_trader_aggregation_page(
        self,
        limit: Optional[int] = None,
        cursor: Optional[int] = None,
        top_traders_ordering: Optional[str] = "volume",
        order: Optional[str] = "desc",
    ) -> TopTraderAggregationResponse:
        """
        Get a single page of top traders by volume, PnL, or account value.

        Parameters
        ----------
        limit : Optional[int]
            Maximum number of results to return
        cursor : Optional[int]
            Cursor for pagination
        top_traders_ordering : Optional[str]
            Ordering criteria: "volume", "pnl", or "accountValue"
        order : Optional[str]
            Sort order ("asc" or "desc")

        Returns
        -------
        TopTraderAggregationResponse
            Single page of top traders with pagination metadata
        """

        params = {
            "limit": limit,
            "cursor": cursor,
            "topTradersOrdering": top_traders_ordering,
            "order": order,
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Make the request
        response = await self._http.get(
            self._build_url(Account.GET_TOP_TRADER_AGGREGATION), params=params
        )

        # Parse the response with Pydantic
        return TopTraderAggregationResponse.model_validate(response)

    async def get_top_trader_aggregation(
        self,
        limit: Optional[int] = 100,
        top_traders_ordering: Optional[str] = "volume",
        order: Optional[str] = "desc",
    ) -> AsyncIterator[TopTraderAggregation]:
        """
        Get all top traders by volume, PnL, or account value.

        Automatically handles pagination.

        Parameters
        ----------
        limit : Optional[int]
            Maximum number of results per page
        top_traders_ordering : Optional[str]
            Ordering criteria: "volume", "pnl", or "accountValue"
        order : Optional[str]
            Sort order ("asc" or "desc")

        Yields
        ------
        TopTraderAggregation
            Top trader entries
        """
        cursor = None

        while True:
            response = await self.get_top_trader_aggregation_page(
                limit=limit,
                cursor=cursor,
                top_traders_ordering=top_traders_ordering,
                order=order,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if not response.next_cursor:
                break

            cursor = response.next_cursor
