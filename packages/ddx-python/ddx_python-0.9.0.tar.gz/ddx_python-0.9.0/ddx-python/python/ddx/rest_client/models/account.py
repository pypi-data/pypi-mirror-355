from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, field_validator
from pydantic.alias_generators import to_camel
from dateutil.parser import parse

from ddx._rust.decimal import Decimal


class TraderUpdate(BaseModel):
    """Trader update data model."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    epoch_id: int
    tx_ordinal: int
    ordinal: int
    withdraw_ddx_rejection: Optional[int] = None
    reason: int
    trader_address: str
    amount: Optional[str] = None
    new_avail_ddx_balance: Optional[str] = None
    new_locked_ddx_balance: Optional[str] = None
    pay_fees_in_ddx: Optional[bool] = None
    block_number: Optional[str] = None
    created_at: datetime

    @field_validator("created_at", mode="before")
    @classmethod
    def parse_datetime(cls, value):
        if isinstance(value, str):
            return parse(value)
        return value


class TraderUpdateHistoryResponse(BaseModel):
    """Response model for trader update history endpoint with cursor pagination."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    value: List[TraderUpdate]
    next_epoch: Optional[int] = None
    next_tx_ordinal: Optional[int] = None
    next_ordinal: Optional[int] = None
    success: bool
    timestamp: int


class StrategyPositionUpdate(BaseModel):
    """Strategy position update data model."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str
    side: Optional[int] = None
    avg_entry_price: Optional[str] = None
    realized_pnl: str


class StrategyUpdate(BaseModel):
    """Strategy update data model."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    epoch_id: int
    tx_ordinal: int
    ordinal: int
    withdraw_rejection: Optional[int] = None
    reason: int
    trader_address: str
    strategy_id_hash: str
    collateral_address: str
    collateral_symbol: str
    amount: str
    new_avail_collateral: Optional[str] = None
    new_locked_collateral: Optional[str] = None
    block_number: Optional[str] = None
    positions: Optional[List[StrategyPositionUpdate]] = None
    created_at: datetime

    @field_validator("created_at", mode="before")
    @classmethod
    def parse_datetime(cls, value):
        if isinstance(value, str):
            return parse(value)
        return value


class StrategyUpdateHistoryResponse(BaseModel):
    """Response model for strategy update history endpoint with cursor pagination."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    value: List[StrategyUpdate]
    next_epoch: Optional[int] = None
    next_tx_ordinal: Optional[int] = None
    next_ordinal: Optional[int] = None
    success: bool
    timestamp: int


class TraderProfile(BaseModel):
    """Trader profile data model."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    trader: str
    avail_ddx: str
    locked_ddx: str
    pay_fees_in_ddx: bool


class TraderProfileResponse(BaseModel):
    """Response model for trader profile endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    value: Optional[TraderProfile] = None
    success: bool
    timestamp: int


class StrategyFee(BaseModel):
    """Strategy fee data model."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    epoch_id: int
    tx_ordinal: int
    ordinal: int
    amount: str
    fee_symbol: str
    symbol: str
    created_at: datetime

    @field_validator("created_at", mode="before")
    @classmethod
    def parse_datetime(cls, value):
        if isinstance(value, str):
            return parse(value)
        return value


class StrategyFeeHistoryResponse(BaseModel):
    """Response model for strategy fee history endpoint with cursor pagination."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    value: List[StrategyFee]
    next_epoch: Optional[int] = None
    next_tx_ordinal: Optional[int] = None
    next_ordinal: Optional[int] = None
    success: bool
    timestamp: int


class Strategy(BaseModel):
    """Trader strategy data model."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    trader: str
    strategy_id_hash: str
    strategy_id: str
    max_leverage: int
    avail_collateral: str
    locked_collateral: str
    frozen: bool


class StrategyResponse(BaseModel):
    """Response model for strategy endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    value: Optional[Strategy] = None
    success: bool
    timestamp: int


class StrategyMetrics(BaseModel):
    """Strategy metrics data model."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    margin_fraction: str
    mmr: str
    leverage: str
    strategy_margin: str
    strategy_value: str


class StrategyMetricsResponse(BaseModel):
    """Response model for strategy metrics endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    value: StrategyMetrics
    success: bool
    timestamp: int


class Position(BaseModel):
    """Position data model."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    trader: str
    symbol: str
    strategy_id_hash: str
    side: int
    balance: str
    avg_entry_price: str
    last_modified_in_epoch: Optional[int] = None


class PositionsResponse(BaseModel):
    """Response model for strategy positions endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    value: List[Position]
    success: bool
    timestamp: int


class StrategyBalanceChangeAggregation(BaseModel):
    """Strategy balance change aggregation data model."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    trader: str
    strategy_id_hash: str
    amount: str
    timestamp: int


class StrategyBalanceChangeAggregationResponse(BaseModel):
    """Response model for strategy balance change aggregation endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    value: List[StrategyBalanceChangeAggregation]
    success: bool
    timestamp: int


class StrategyFundingRatePaymentAggregation(BaseModel):
    """Strategy funding rate payment aggregation data model."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    trader: str
    strategy_id_hash: str
    amount: str
    timestamp: int


class StrategyFundingRatePaymentAggregationResponse(BaseModel):
    """Response model for strategy funding rate payment aggregation endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    value: List[StrategyFundingRatePaymentAggregation]
    success: bool
    timestamp: int


class StrategyRealizedPnlAggregation(BaseModel):
    """Strategy realized PNL aggregation data model."""

    model_config = ConfigDict(populate_by_name=True)

    trader: str
    strategy_id_hash: str
    amount: str
    timestamp: int


class StrategyRealizedPnlAggregationResponse(BaseModel):
    """Response model for strategy realized PNL aggregation endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    value: List[StrategyRealizedPnlAggregation]
    success: bool
    timestamp: int


class TradeMiningRewardAggregation(BaseModel):
    """Trade mining reward aggregation data model."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    trader: str
    amount: str
    timestamp: int


class TradeMiningRewardAggregationResponse(BaseModel):
    """Response model for trade mining reward aggregation endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    value: List[TradeMiningRewardAggregation]
    success: bool
    timestamp: int


class TopTraderAggregation(BaseModel):
    """Top trader aggregation data model."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    trader: str
    volume: Optional[str] = None
    realized_pnl: Optional[str] = None
    account_value: Optional[str] = None


class TopTraderAggregationResponse(BaseModel):
    """Response model for top trader aggregation endpoint with cursor pagination."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    value: List[TopTraderAggregation]
    next_cursor: Optional[int] = None
    success: bool
    timestamp: int
