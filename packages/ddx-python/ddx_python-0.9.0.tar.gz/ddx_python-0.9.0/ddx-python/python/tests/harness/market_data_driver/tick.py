"""
Tick module.
"""

from enum import Enum
from typing import Dict, Tuple

import pandas as pd
from attrs import define, field
from ddx._rust.common import ProductSymbol
from ddx._rust.decimal import Decimal


class TickedTxResponsesType(int, Enum):
    """
    Types of (expected, actual) responses for txs triggered by a tick.
    """

    INDEX_PRICE = 1
    PRICE_CHECKPOINT = 2
    ADVANCE_SETTLEMENT_EPOCH = 4
    ADVANCE_EPOCH = 6
    UPDATE_PRODUCT_LISTINGS = 7


@define
class Tick:
    """
    Defines a Tick.

    Market data construct comprising a timestamp, symbol, and underlying price.

    Attributes:
        dt (pd.Timestamp): Timestamp (1s frequency).
        prices (Dict[ProductSymbol, Decimal]): Symbol <> underlying price mapping.
        ticked_tx_responses (Dict[TickedTxResponsesType, tuple]):
            (expected, actual) responses for txs triggered by this tick.
    """

    dt: pd.Timestamp
    prices: Dict[ProductSymbol, Decimal]
    ticked_tx_responses: Dict[TickedTxResponsesType, Tuple]
