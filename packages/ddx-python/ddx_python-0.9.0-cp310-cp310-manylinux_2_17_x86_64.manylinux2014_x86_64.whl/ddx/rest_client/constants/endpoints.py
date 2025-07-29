from enum import Enum


class Market(str, Enum):
    """Enum containing all market-related endpoint paths."""

    GET_MARK_PRICE_HISTORY = "/exchange/api/v1/mark_prices"
    GET_ORDER_BOOK_L3 = "/exchange/api/v1/order_book"
    GET_ORDER_UPDATE_HISTORY = "/exchange/api/v1/order_updates"
    GET_FUNDING_RATE_HISTORY = "/stats/api/v1/funding_rate_history"
    GET_TICKERS = "/stats/api/v1/markets/tickers"
    GET_OPEN_INTEREST_HISTORY = "/stats/api/v1/open_interest_history"
    GET_PRICE_CHECKPOINTS = "/stats/api/v1/price_checkpoints"
    GET_MARKETS = "/stats/api/v1/markets"
    GET_VOLUME_AGGREGATION = "/stats/api/v1/aggregations/volume"
    GET_FUNDING_RATE_COMPARISON_AGGREGATION = (
        "/stats/api/v1/aggregations/funding_rate_comparison"
    )
    GET_FEE_AGGREGATION = "/stats/api/v1/aggregations/fees"
    GET_ORDER_BOOK_L2 = "/stats/api/v1/markets/order_book/L2"


class Account(str, Enum):
    """Enum containing all account-related endpoint paths."""

    GET_TRADER_UPDATE_HISTORY = "/exchange/api/v1/trader_updates"
    GET_STRATEGY_UPDATE_HISTORY = "/exchange/api/v1/strategy_updates"
    GET_TRADER_PROFILE = "/stats/api/v1/account/{trader}"
    GET_STRATEGY_FEE_HISTORY = (
        "/stats/api/v1/account/{trader}/strategy/{strategyId}/fees"
    )
    GET_STRATEGY = "/stats/api/v1/account/{trader}/strategy/{strategyId}"
    GET_STRATEGY_METRICS = (
        "/stats/api/v1/account/{trader}/strategy/{strategyId}/metrics"
    )
    GET_POSITIONS = "/stats/api/v1/account/{trader}/strategy/{strategyId}/positions"
    GET_STRATEGY_BALANCE_CHANGE_AGGREGATION = (
        "/stats/api/v1/aggregations/account/{trader}/strategy/{strategyId}/balance"
    )
    GET_STRATEGY_FUNDING_RATE_PAYMENT_AGGREGATION = "/stats/api/v1/aggregations/account/{trader}/strategy/{strategyId}/funding_rate_payments"
    GET_STRATEGY_REALIZED_PNL_AGGREGATION = (
        "/stats/api/v1/aggregations/account/{trader}/strategy/{strategyId}/realized_pnl"
    )
    GET_TRADE_MINING_REWARD_AGGREGATION = (
        "/stats/api/v1/aggregations/account/{trader}/trade_mining_rewards"
    )
    GET_TOP_TRADER_AGGREGATION = "/stats/api/v1/aggregations/traders"


class System(str, Enum):
    """Enum containing all system-related endpoint paths."""

    GET_EXCHANGE_INFO = "/exchange/api/v1/exchange_info"
    GET_TEST_CONNECTIVITY = "/exchange/api/v1/ping"
    GET_SYMBOLS = "/exchange/api/v1/symbols"
    GET_SERVER_TIME = "/exchange/api/v1/time"
    GET_EPOCH_HISTORY = "/stats/api/v1/epochs"
    GET_INSURANCE_FUND_HISTORY = "/stats/api/v1/insurance_fund"
    GET_SPECS = "/stats/api/v1/specs"
    GET_EXCHANGE_STATUS = "/stats/api/v1/status/exchange"
    GET_DDX_SUPPLY = "/stats/api/v1/supply"
    GET_TRADABLE_PRODUCTS = "/stats/api/v1/tradable_products"
    GET_COLLATERAL_AGGREGATION = "/stats/api/v1/aggregations/collateral"
    GET_DDX_AGGREGATION = "/stats/api/v1/aggregations/ddx"
    GET_INSURANCE_FUND_AGGREGATION = "/stats/api/v1/aggregations/insurance_fund"
    GET_DEPLOYMENT_INFO = "/contract-server/addresses"


class Trade(str, Enum):
    """Enum containing all trading-related endpoint paths."""

    ENCRYPTION_KEY = "/v2/encryption-key"
    SUBMIT_REQUEST = "/v2/request"


class OnChain(str, Enum):
    """Enum containing all on-chain-related endpoint paths."""

    KYC_AUTH = "/kyc/v1/kyc-auth"
    PROOF = "/v2/proof"
