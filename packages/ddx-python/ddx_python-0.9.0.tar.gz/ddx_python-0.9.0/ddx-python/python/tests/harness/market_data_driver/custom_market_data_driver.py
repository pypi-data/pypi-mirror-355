"""
CustomMarketDataDriver module.
"""

import datetime
import pprint

import numpy as np
import pandas as pd
from aiohttp import ClientSession
from attrs import define
from ddx.common.logging import data_logger
from ddx._rust.common import ProductSymbol
from ddx._rust.decimal import Decimal
from tests.harness.market_data_driver.market_data_driver import \
    MarketDataDriver

logger = data_logger(__name__)
pp = pprint.PrettyPrinter(indent=4)


@define
class CustomMarketDataDriver(MarketDataDriver):
    """
    Defines a CustomMarketDataDriver.

    A CustomMarketDataDriver is a MarketDataDriver that is driven by a custom data input.

    Attributes:
        symbols_feed (dict[ProductSymbol, str]): symbol <> underlying price ticker mapping.
        start_timestamp (datetime.datetime): Starting timestamp to build the custom market data dataframe.
        time_frame (str): Initial sampling frequency for market data which will then be upsampled to 1s.
        client (ClientSession): HTTP client connection.
        timestamps (dict[ProductSymbol, pd.DatetimeIndex]): symbol <> timestamp mapping. The list of timestamps are the indices for the market data for this symbol.
        prices (dict[ProductSymbol, list[float]]): symbol <> prices mapping. The list of prices are the column values corresponding to each timestamp for the market data for this symbol.
    """

    symbols_feed: dict[ProductSymbol, str]
    start_timestamp: datetime.datetime
    time_frame: str
    client: ClientSession
    timestamps: dict[ProductSymbol, pd.DatetimeIndex]
    prices: dict[ProductSymbol, list[float]]

    @classmethod
    def from_price_ranges(
        cls,
        symbols_feed: dict[ProductSymbol, str],
        time_frame: str,
        client: ClientSession,
        start_timestamp: pd.Timestamp,
        duration: str,
        price_ranges: dict[ProductSymbol, tuple[Decimal, Decimal]],
    ):
        """
        Construct a driver for market data from a custom data input given a starting timestamp, duration, and
        a start/stop range of prices.

        Parameters
        ----------
        symbols_feed : dict[ProductSymbol, str]
            Symbol <> underlying price ticker mapping.
        time_frame : str
            Initial sampling frequency for market data which will then be upsampled to 1s.
        client : ClientSession
            HTTP client connection.
        start_timestamp : pd.Timestamp
            Starting timestamp to build the custom market data dataframe.
        duration : str
            Length of time the market data dataframe should span starting with the start_timestamp.
        price_ranges : dict[ProductSymbol, tuple[Decimal, Decimal]],
            Symbol <> price range mapping. Each price range is a tuple of (starting_price, ending_price), and the
            resulting prices are a simple linear interpolation between these two given the timestamps that are derived
            from the start_timestamp and duration.
        """

        timestamps = {}
        prices = {}
        for symbol in symbols_feed:
            # Loop through each symbol.

            # Construct timestamps as an equally-spaced date-series from the start_timestamp to the end_timestamp
            # (start_timestamp + duration), given a 1m frequency.
            timestamps[symbol] = pd.date_range(
                start=start_timestamp,
                end=start_timestamp + pd.Timedelta(duration),
                freq=time_frame,
            )

            # Construct a linear interpolation between the start and ending price ranges for each timestamp.
            prices[symbol] = list(
                np.linspace(
                    float(price_ranges[symbol][0]),
                    float(price_ranges[symbol][1]),
                    len(timestamps[symbol]),
                ).round(6)
            )

        return cls(
            symbols_feed,
            start_timestamp.to_pydatetime().replace(tzinfo=datetime.timezone.utc),
            time_frame,
            client,
            timestamps,
            prices,
        )

    def generate_df(self):
        """
        Generate a market data dataframe to drive the simulation. This function is implemented uniquely by the
        various types of MarketDataDrivers.
        """

        for symbol in self.symbols_feed:
            assert len(self.timestamps[symbol]) == len(self.prices[symbol])
            logger.info(
                f"{symbol} (Timestamps, Prices):\n{pprint.pformat(list(zip(self.timestamps[symbol], self.prices[symbol])))}"
            )

        dfs = []
        for k, v in self.symbols_feed.items():
            # Loop through each symbol to fetch.

            # Prepare dataframe with data.
            columns = [
                f"{k}_close",
            ]
            df = pd.DataFrame(self.prices[k], index=self.timestamps[k], columns=columns)
            df[f"{k}_symbol"] = v
            dfs.append(df)

        # Return the symbol dataframes concatenated with each other and upsampled to 1s frequency.
        return pd.concat(dfs, axis=1).resample("1s").ffill()
