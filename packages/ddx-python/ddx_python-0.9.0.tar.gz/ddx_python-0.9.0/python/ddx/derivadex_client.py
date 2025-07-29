"""
DerivaDEX Client
"""
from typing import Optional

from web3 import Web3
from web3.middleware import geth_poa_middleware

from ddx.realtime_client import RealtimeClient
from ddx.rest_client.resources.account_resource import AccountResource
from ddx.rest_client.resources.market_resource import MarketResource
from ddx.rest_client.resources.on_chain_resource import OnChainResource
from ddx.rest_client.resources.system_resource import SystemResource
from ddx.rest_client.resources.trade_resource import TradeResource
from ddx.rest_client.http.http_client import HTTPClient


class DerivaDEXClient:
    """
    Main client for interacting with the DerivaDEX API.

    This client provides access to all DerivaDEX API endpoints through
    various resource objects and supports both REST and WebSocket APIs.
    It can be used as an async context manager to ensure proper resource cleanup.

    Attributes
    ----------
    account : AccountResource
        Access to account-related operations and data.
    market : MarketResource
        Access to market-related operations and data
    on_chain : OnChainResource
        Access to on-chain operations
    system : SystemResource
        Access to system-related operations and data
    trade : TradeResource
        Access to trading operations
    web3_account : Account
        The Web3 account used for signing transactions
    """

    def __init__(
        self,
        base_url: str,
        rpc_url: str,
        contract_deployment: str,
        private_key: str = None,
        mnemonic: str = None,
        timeout: int = 30,
    ) -> None:
        """
        Initialize the client.

        Parameters
        ----------
        base_url : str
            Base URL for webserver
        rpc_url : str
            RPC URL for webserver
        contract_deployment : str
            Type of contract deployment (e.g. "mainnet")
        private_key : str, optional
            Ethereum private key for user
        mnemonic : str, optional
            Ethereum mnemonic for user
        timeout : int, default=30
            Timeout in seconds for HTTP requests

        Raises
        ------
        ValueError
            If neither private_key nor mnemonic is provided
        """

        if not private_key and not mnemonic:
            raise ValueError("Either private_key or mnemonic must be provided")

        self._base_url = base_url

        # Initialize HTTP client
        self._http = HTTPClient(timeout)

        self._contract_deployment = contract_deployment

        # These will be initialized when needed
        self._chain_id: Optional[int] = None
        self._verifying_contract: Optional[str] = None

        # Initialize web3 service
        self.w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 60}))

        if contract_deployment == "geth":
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        # Initialize web3 account from private key or mnemonic
        if private_key is not None:
            self.web3_account = self.w3.eth.account.from_key(private_key)
        else:
            self.w3.eth.account.enable_unaudited_hdwallet_features()
            self.web3_account = self.w3.eth.account.from_mnemonic(mnemonic)

        # Set default account for send transactions
        self.w3.eth.defaultAccount = self.web3_account.address

        # Initialize resources (lazy loading)
        self._account: Optional[AccountResource] = None
        self._market: Optional[MarketResource] = None
        self._on_chain: Optional[OnChainResource] = None
        self._system: Optional[SystemResource] = None
        self._trade: Optional[TradeResource] = None

    async def __aenter__(self) -> "DerivaDEXClient":
        await self._http.__aenter__()

        # Get deployment configuration
        deployment_info = await self.system.get_deployment_info(
            self._contract_deployment
        )
        self._chain_id = deployment_info.chain_id
        self._verifying_contract = deployment_info.addresses.derivadex_address

        # Initialize and start WebSocket client
        # We do this here rather than lazy loading because we want
        # to ensure the connection is established when using the context manager
        self._ws = RealtimeClient()
        await self._ws.connect()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        # Stop WebSocket client if it was started
        if self._ws is not None:
            await self._ws.disconnect()
        await self._http.__aexit__(exc_type, exc_val, exc_tb)

    @property
    def ws(self) -> RealtimeClient:
        """
        Access WebSocket functionality.

        Returns
        -------
        RealtimeClient
            The WebSocket Realtime API client instance

        Raises
        ------
        RuntimeError
            If accessed outside of context manager
        """

        if not hasattr(self, "_ws"):
            raise RuntimeError("WebSocket client must be used within context manager")

        return self._ws

    @property
    def account(self) -> AccountResource:
        """
        Access to account-related operations and data.

        Returns
        -------
        AccountResource
            The account resource instance, initialized on first access
        """

        if self._account is None:
            self._account = AccountResource(self._http, self._base_url)

        return self._account

    @property
    def market(self) -> MarketResource:
        """
        Access to market-related operations and data

        Returns
        -------
        MarketResource
            The market resource instance, initialized on first access
        """

        if self._market is None:
            self._market = MarketResource(self._http, self._base_url)

        return self._market

    @property
    def system(self) -> SystemResource:
        """
        Access to system-related operations and data

        Returns
        -------
        SystemResource
            The system resource instance, initialized on first access
        """

        if self._system is None:
            self._system = SystemResource(self._http, self._base_url)

        return self._system

    @property
    def on_chain(self) -> OnChainResource:
        """
        Access on-chain operations.

        Returns
        -------
        OnChainResource
            The on-chain resource instance, initialized on first access
        """

        if self._on_chain is None:
            self._on_chain = OnChainResource(
                self._http,
                self._base_url,
                self.web3_account,
                self.w3,
                self._verifying_contract,
            )

        return self._on_chain

    @property
    def trade(self) -> TradeResource:
        """
        Access to trading operations

        Returns
        -------
        TradeResource
            The trade resource instance, initialized on first access
        """

        if self._trade is None:
            self._trade = TradeResource(
                self._http,
                self._base_url,
                self.web3_account,
                self._chain_id,
                self._verifying_contract,
            )

        return self._trade
