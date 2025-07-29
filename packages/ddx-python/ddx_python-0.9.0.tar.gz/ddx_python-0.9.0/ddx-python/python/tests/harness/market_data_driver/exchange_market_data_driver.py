"""
ExchangeMarketDataDriver module.
"""

import datetime

import ccxt
import pandas as pd
from aiohttp import ClientSession
from attrs import define
from ddx._rust.common import ProductSymbol
from tests.harness.market_data_driver.market_data_driver import \
    MarketDataDriver


@define
class ExchangeMarketDataDriver(MarketDataDriver):
    """
    Defines a ExchangeMarketDataDriver.

    An ExchangeMarketDataDriver is a MarketDataDriver that pulls OHLCV data from an exchange.

    Attributes:
        symbols_feed (dict[ProductSymbol, str]): symbol <> underlying price ticker mapping
        start_timestamp (datetime.datetime): start timestamp for market data
        time_frame (str): initial sampling frequency for market data which will then be upsampled to 1s
        client (ClientSession): HTTP client connection
        exchange_venue (str): exchange venue name to pull data from
    """

    symbols_feed: dict[ProductSymbol, str]
    start_timestamp: datetime.datetime
    time_frame: str
    client: ClientSession
    exchange_venue: str

    def generate_df(self):
        """
        Generate a market data dataframe to drive the simulation. This function is implemented uniquely by the
        various types of MarketDataDrivers.
        """

        # Get exchange CCXT handler.
        exchange = getattr(ccxt, self.exchange_venue)()

        # Check if the symbols are available on the exchange.
        exchange.load_markets()
        if not all(
            [symbol in exchange.symbols for symbol in list(self.symbols_feed.values())]
        ):
            raise Exception("Not supported market symbols.")

        dfs = []
        for k, v in self.symbols_feed.items():
            # Loop through each symbol to fetch.

            # Fetch OHLCV data for the particular symbol being evaluated.
            data = exchange.fetch_ohlcv(v, timeframe=self.time_frame)

            # Prepare dataframe with data.
            columns = [
                f"{k}_timestamp",
                f"{k}_open",
                f"{k}_high",
                f"{k}_low",
                f"{k}_close",
                f"{k}_volume",
            ]
            df = pd.DataFrame(data, columns=columns)
            df[f"{k}_symbol"] = v
            df["date"] = pd.to_datetime(df[f"{k}_timestamp"] / 1_000, unit="s")
            df.set_index(["date"], inplace=True)
            dfs.append(df)

        # Return the symbol dataframes concatenated with each other and upsampled to 1s frequency.
        return pd.concat(dfs, axis=1).resample("1s").ffill()
