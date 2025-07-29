from typing import Optional, AsyncIterator

from ddx.rest_client.constants.endpoints import System
from ddx.rest_client.resources.base_resource import BaseResource
from ddx.rest_client.models.system import (
    ExchangeInfoResponse,
    SymbolsResponse,
    ServerTimeResponse,
    EpochHistoryResponse,
    Epoch,
    InsuranceFundHistoryResponse,
    InsuranceFundUpdate,
    SpecsResponse,
    ExchangeStatusResponse,
    DDXSupplyResponse,
    TradableProductsResponse,
    TradableProduct,
    CollateralAggregationResponse,
    CollateralAggregation,
    DDXAggregationResponse,
    DDXAggregationItem,
    InsuranceFundAggregationResponse,
    InsuranceFundAggregation,
    DeploymentInfo,
)


class SystemResource(BaseResource):
    """
    System-related operations and data access.

    Provides access to exchange configuration, system status, and other
    system-related information through the API endpoints.
    """

    async def get_exchange_info(self) -> ExchangeInfoResponse:
        """
        Get global exchange configuration.

        Returns
        -------
        ExchangeInfoResponse
            Exchange configuration information
        """

        # Make the request
        response = await self._http.get(self._build_url(System.GET_EXCHANGE_INFO))

        # Parse the response with Pydantic
        return ExchangeInfoResponse.model_validate(response)

    async def test_connectivity(self) -> bool:
        """
        Test connectivity to the API.

        Simple ping to check if the API is responding.

        Returns
        -------
        bool
            True if the API is responding, False otherwise
        """

        try:
            # Make the request
            await self._http.get(self._build_url(System.GET_TEST_CONNECTIVITY))

            # If we get here, the request was successful
            return True
        except Exception as e:
            self._logger.error(f"Connectivity test failed: {str(e)}")
            return False

    async def get_symbols(
        self,
        kind: Optional[int] = None,
        is_active: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> SymbolsResponse:
        """
        Get list of available trading products.

        Parameters
        ----------
        kind : Optional[int]
            Filter by type of product (0: Market, 1: MarketGateway)
        is_active : Optional[bool]
            Filter by active state
        limit : Optional[int]
            Maximum number of results to return
        offset : Optional[int]
            Offset for pagination

        Returns
        -------
        SymbolsResponse
            List of tradable products
        """

        params = {
            "kind": kind,
            "isActive": is_active,
            "limit": limit,
            "offset": offset,
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Make the request
        response = await self._http.get(
            self._build_url(System.GET_SYMBOLS), params=params
        )

        # Parse the response with Pydantic
        return SymbolsResponse.model_validate(response)

    async def get_server_time(self) -> ServerTimeResponse:
        """
        Get server time for clock synchronization.

        Returns
        -------
        ServerTimeResponse
            Server time in milliseconds
        """

        # Make the request
        response = await self._http.get(self._build_url(System.GET_SERVER_TIME))

        # Parse the response with Pydantic
        return ServerTimeResponse.model_validate(response)

    async def get_epoch_history_page(
        self,
        epoch: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> EpochHistoryResponse:
        """
        Get a single page of epoch timetable and paging cursors.

        Parameters
        ----------
        epoch : Optional[int]
            The epoch boundary used when fetching the next timeseries page
        limit : Optional[int]
            The number of rows to return
        offset : Optional[int]
            The offset of returned rows

        Returns
        -------
        EpochHistoryResponse
            Single page of epochs data
        """

        params = {
            "epoch": epoch,
            "limit": limit,
            "offset": offset,
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Make the request
        response = await self._http.get(
            self._build_url(System.GET_EPOCH_HISTORY), params=params
        )

        # Parse the response with Pydantic
        return EpochHistoryResponse.model_validate(response)

    async def get_epoch_history(
        self,
        epoch: Optional[int] = None,
        limit: Optional[int] = 100,
    ) -> AsyncIterator[Epoch]:
        """
        Get all epochs.

        Automatically handles pagination using offset.

        Parameters
        ----------
        epoch : Optional[int]
            The epoch boundary used when fetching the next timeseries page
        limit : Optional[int]
            The number of rows to return per page

        Yields
        ------
        Epoch
            Epoch entries
        """
        offset = 0

        while True:
            response = await self.get_epoch_history_page(
                epoch=epoch,
                limit=limit,
                offset=offset,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            # This endpoint uses offset-based pagination
            if len(response.value) < limit:
                break

            offset += len(response.value)

    async def get_insurance_fund_history_page(
        self,
        limit: Optional[int] = None,
        epoch: Optional[int] = None,
        tx_ordinal: Optional[int] = None,
        order: Optional[str] = None,
        symbol: Optional[str] = None,
    ) -> InsuranceFundHistoryResponse:
        """
        Get a single page of insurance fund balance history.

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
            Filter by symbol

        Returns
        -------
        InsuranceFundHistoryResponse
            Single page of insurance fund updates with pagination metadata
        """

        params = {
            "limit": limit,
            "epoch": epoch,
            "txOrdinal": tx_ordinal,
            "order": order,
            "symbol": symbol,
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Make the request
        response = await self._http.get(
            self._build_url(System.GET_INSURANCE_FUND_HISTORY), params=params
        )

        # Parse the response with Pydantic
        return InsuranceFundHistoryResponse.model_validate(response)

    async def get_insurance_fund_history(
        self,
        limit: Optional[int] = 100,
        order: Optional[str] = None,
        symbol: Optional[str] = None,
    ) -> AsyncIterator[InsuranceFundUpdate]:
        """
        Get all insurance fund balance history.

        Automatically handles pagination.

        Parameters
        ----------
        limit : Optional[int]
            Maximum number of results per page
        order : Optional[str]
            Sort order ("asc" or "desc")
        symbol : Optional[str]
            Filter by symbol

        Yields
        ------
        InsuranceFundUpdate
            Insurance fund update entries
        """
        epoch = None
        tx_ordinal = None

        while True:
            response = await self.get_insurance_fund_history_page(
                limit=limit,
                epoch=epoch,
                tx_ordinal=tx_ordinal,
                order=order,
                symbol=symbol,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if not response.next_epoch:
                break

            epoch = response.next_epoch
            tx_ordinal = response.next_tx_ordinal

    async def get_specs(
        self,
        kind: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> SpecsResponse:
        """
        Get current operator configuration settings.

        Parameters
        ----------
        kind : Optional[int]
            Filter by type of spec update (0: Market, 1: MarketGateway)
        limit : Optional[int]
            Maximum number of results to return
        offset : Optional[int]
            Number of results to skip

        Returns
        -------
        SpecsResponse
            Operator configuration settings
        """

        params = {
            "kind": kind,
            "limit": limit,
            "offset": offset,
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Make the request
        response = await self._http.get(
            self._build_url(System.GET_SPECS), params=params
        )

        # Parse the response with Pydantic
        return SpecsResponse.model_validate(response)

    async def get_exchange_status(self) -> ExchangeStatusResponse:
        """
        Get high-level exchange status information.

        Returns
        -------
        ExchangeStatusResponse
            Exchange status information including current epoch,
            latest on-chain checkpoint, and active addresses
        """

        # Make the request
        response = await self._http.get(self._build_url(System.GET_EXCHANGE_STATUS))

        # Parse the response with Pydantic
        return ExchangeStatusResponse.model_validate(response)

    async def get_ddx_supply(self) -> DDXSupplyResponse:
        """
        Get total DDX circulation information.

        Returns
        -------
        DDXSupplyResponse
            DDX supply information
        """

        # Make the request
        response = await self._http.get(self._build_url(System.GET_DDX_SUPPLY))

        # Parse the response with Pydantic
        return DDXSupplyResponse.model_validate(response)

    async def get_tradable_products_page(
        self,
        kind: Optional[int] = None,
        is_active: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> TradableProductsResponse:
        """
        Get a single page of available trading products.

        Parameters
        ----------
        kind : Optional[int]
            The type of product (0: Market, 1: MarketGateway)
        is_active : Optional[bool]
            Filter by active state (true/false)
        limit : Optional[int]
            Maximum number of results to return
        offset : Optional[int]
            Offset for pagination

        Returns
        -------
        TradableProductsResponse
            Single page of available trading products
        """

        params = {
            "kind": kind,
            "isActive": is_active,
            "limit": limit,
            "offset": offset,
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Make the request
        response = await self._http.get(
            self._build_url(System.GET_TRADABLE_PRODUCTS), params=params
        )

        # Parse the response with Pydantic
        return TradableProductsResponse.model_validate(response)

    async def get_tradable_products(
        self,
        kind: Optional[int] = None,
        is_active: Optional[bool] = None,
        limit: Optional[int] = 100,
    ) -> AsyncIterator[TradableProduct]:
        """
        Get all available trading products.

        Automatically handles pagination using offset.

        Parameters
        ----------
        kind : Optional[int]
            The type of product (0: Market, 1: MarketGateway)
        is_active : Optional[bool]
            Filter by active state (true/false)
        limit : Optional[int]
            Maximum number of results per page

        Yields
        ------
        TradableProduct
            Trading product entries
        """

        offset = 0

        while True:
            response = await self.get_tradable_products_page(
                kind=kind,
                is_active=is_active,
                limit=limit,
                offset=offset,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if len(response.value) < limit:
                break

            offset += len(response.value)

    async def get_collateral_aggregation_page(
        self,
        aggregation_period: Optional[str] = None,
        starting_value: Optional[float] = None,
        from_epoch: Optional[int] = None,
        to_epoch: Optional[int] = None,
    ) -> CollateralAggregationResponse:
        """
        Get a single page of collateral aggregation data.

        Parameters
        ----------
        aggregation_period : Optional[str]
            The period for aggregation ("week", "day", "hour", "minute")
        starting_value : Optional[float]
            The partial total for rolling aggregation paging
        from_epoch : Optional[int]
            The starting epoch for filtering
        to_epoch : Optional[int]
            The ending epoch for filtering

        Returns
        -------
        CollateralAggregationResponse
            Single page of collateral aggregation data with pagination metadata
        """

        params = {
            "aggregationPeriod": aggregation_period,
            "startingValue": starting_value,
            "fromEpoch": from_epoch,
            "toEpoch": to_epoch,
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Make the request
        response = await self._http.get(
            self._build_url(System.GET_COLLATERAL_AGGREGATION), params=params
        )

        # Parse the response with Pydantic
        return CollateralAggregationResponse.model_validate(response)

    async def get_collateral_aggregation(
        self,
        aggregation_period: Optional[str] = None,
        from_epoch: Optional[int] = None,
        to_epoch: Optional[int] = None,
    ) -> AsyncIterator[CollateralAggregation]:
        """
        Get all collateral aggregation data.

        Automatically handles pagination using starting_value.

        Parameters
        ----------
        aggregation_period : Optional[str]
            The period for aggregation ("week", "day", "hour", "minute")
        from_epoch : Optional[int]
            The starting epoch for filtering
        to_epoch : Optional[int]
            The ending epoch for filtering

        Yields
        ------
        CollateralAggregation
            Collateral aggregation entries
        """

        starting_value = None

        while True:
            response = await self.get_collateral_aggregation_page(
                aggregation_period=aggregation_period,
                starting_value=starting_value,
                from_epoch=from_epoch,
                to_epoch=to_epoch,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if not response.next_starting_value:
                break

            starting_value = float(response.next_starting_value)

    async def get_ddx_aggregation_page(
        self,
        aggregation_period: Optional[str] = "day",
        starting_value: Optional[int] = None,
        from_epoch: Optional[int] = None,
        to_epoch: Optional[int] = None,
    ) -> DDXAggregationResponse:
        """
        Get a single page of DDX aggregation data.

        Parameters
        ----------
        aggregation_period : Optional[str]
            The period for aggregation ("week", "day", "hour", "minute")
        starting_value : Optional[int]
            The partial total for rolling aggregation paging
        from_epoch : Optional[int]
            The starting epoch for filtering
        to_epoch : Optional[int]
            The ending epoch for filtering

        Returns
        -------
        DDXAggregationResponse
            Single page of DDX aggregation data with pagination metadata
        """

        params = {
            "aggregationPeriod": aggregation_period,
            "startingValue": starting_value,
            "fromEpoch": from_epoch,
            "toEpoch": to_epoch,
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Make the request
        response = await self._http.get(
            self._build_url(System.GET_DDX_AGGREGATION), params=params
        )

        # Parse the response with Pydantic
        return DDXAggregationResponse.model_validate(response)

    async def get_ddx_aggregation(
        self,
        aggregation_period: Optional[str] = "day",
        from_epoch: Optional[int] = None,
        to_epoch: Optional[int] = None,
    ) -> AsyncIterator[DDXAggregationItem]:
        """
        Get all DDX aggregation data.

        Automatically handles pagination using starting_value.

        Parameters
        ----------
        aggregation_period : Optional[str]
            The period for aggregation ("week", "day", "hour", "minute")
        from_epoch : Optional[int]
            The starting epoch for filtering
        to_epoch : Optional[int]
            The ending epoch for filtering

        Yields
        ------
        DdxAggregationItem
            DDX aggregation entries
        """

        starting_value = None

        while True:
            response = await self.get_ddx_aggregation_page(
                aggregation_period=aggregation_period,
                starting_value=starting_value,
                from_epoch=from_epoch,
                to_epoch=to_epoch,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if not response.next_starting_value:
                break

            starting_value = response.next_starting_value

    async def get_insurance_fund_aggregation_page(
        self,
        aggregation_period: Optional[str] = "day",
        starting_value: Optional[str] = None,
        from_epoch: Optional[int] = None,
        to_epoch: Optional[int] = None,
    ) -> InsuranceFundAggregationResponse:
        """
        Get a single page of insurance fund aggregation data.

        Parameters
        ----------
        aggregation_period : Optional[str]
            The period for aggregation ("week", "day", "hour", "minute")
        starting_value : Optional[str]
            The partial total for rolling aggregation
        from_epoch : Optional[int]
            Filter by start epoch
        to_epoch : Optional[int]
            Filter by end epoch

        Returns
        -------
        InsuranceFundAggregationResponse
            Single page of insurance fund aggregation data
        """

        params = {
            "aggregationPeriod": aggregation_period,
            "startingValue": starting_value,
            "fromEpoch": from_epoch,
            "toEpoch": to_epoch,
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Make the request
        response = await self._http.get(
            self._build_url(System.GET_INSURANCE_FUND_AGGREGATION), params=params
        )

        # Parse the response with Pydantic
        return InsuranceFundAggregationResponse.model_validate(response)

    async def get_insurance_fund_aggregation(
        self,
        aggregation_period: Optional[str] = "day",
        from_epoch: Optional[int] = None,
        to_epoch: Optional[int] = None,
    ) -> AsyncIterator[InsuranceFundAggregation]:
        """
        Get all insurance fund aggregation data.

        Automatically handles pagination with rolling aggregation.

        Parameters
        ----------
        aggregation_period : Optional[str]
            The period for aggregation ("week", "day", "hour", "minute")
        from_epoch : Optional[int]
            Filter by start epoch
        to_epoch : Optional[int]
            Filter by end epoch

        Yields
        ------
        InsuranceFundAggregation
            Insurance fund aggregation entries
        """

        starting_value = None

        while True:
            response = await self.get_insurance_fund_aggregation_page(
                aggregation_period=aggregation_period,
                starting_value=starting_value,
                from_epoch=from_epoch,
                to_epoch=to_epoch,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if not response.next_starting_value:
                break

            starting_value = response.next_starting_value

    async def get_deployment_info(self, contract_deployment: str) -> DeploymentInfo:
        """
        Get deployment information including contract addresses.

        Parameters
        ----------
        contract_deployment : str, default="testnet"
            The deployment environment to get information for

        Returns
        -------
        DeploymentInfo
            Deployment information including contract addresses

        Raises
        ------
        HTTPError
            If the request fails
        """

        params = {"contractDeployment": contract_deployment}

        # Make the request
        response = await self._http.get(
            self._build_url(System.GET_DEPLOYMENT_INFO), params=params
        )

        return DeploymentInfo.model_validate(response)
