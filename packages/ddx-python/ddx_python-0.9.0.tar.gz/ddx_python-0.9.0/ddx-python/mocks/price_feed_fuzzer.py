import json
import random
import time
from os import environ
import coloredlogs
import numpy as np
import verboselogs
from flask import Flask
from flask.helpers import make_response
from pathlib import Path

from ddx._rust.common import ProductSymbol
from ddx._rust.decimal import Decimal

from ddx.common.utils import ComplexOutputEncoder


fmt_str = "[%(asctime)s] %(levelname)s @ line %(lineno)d: %(message)s"
log_level = environ.get("PYTHON_LOG").upper() if "PYTHON_LOG" in environ else "VERBOSE"
coloredlogs.install(
    fmt="%(asctime)s,%(msecs)03d %(levelname)s %(message)s",
    level=log_level,
)
logger = verboselogs.VerboseLogger(__name__)

maybe_seed = environ.get("RNG_SEED")
if maybe_seed:
    random.seed(int(maybe_seed))

DISTRIBUTIONS = ["uniform", "gauss"]


def compute_distribution(
    distribution: str, low_price: Decimal, high_price: Decimal, tick_size: Decimal
):
    match distribution:
        case "uniform":
            return random.uniform(low_price, high_price).quantize(tick_size)
        case "gauss":
            clamp = lambda val: (
                low_price
                if val < low_price
                else val
                if high_price > val
                else high_price
            )
            mu = (high_price + low_price) / 2
            sigma = (high_price - mu) / 5
            return clamp(random.gauss(mu, sigma)).quantize(tick_size)
        case _:
            raise Exception(f"Distribution {distribution} not supported.")


class MarketFuzzer:
    def __init__(
        self,
        symbol: ProductSymbol,
        low_price: Decimal,
        high_price: Decimal,
        tick_size: int,
        distribution: str,
        p_regime_refresh: Decimal,
        regime_range: Decimal,
    ):
        if distribution not in DISTRIBUTIONS:
            raise ValueError(f"{self.distribution} is not a supported distribution")

        self.symbol = symbol
        self.low_price = low_price
        self.high_price = high_price
        self.tick_size = tick_size
        self.distribution = distribution
        self.p_regime_refresh = p_regime_refresh
        self.regime_range = regime_range
        self.timestamp = 1
        self.prev_price = 0

    def __repr__(self):
        return f"MarketFuzzer({self.symbol}, {self.low_price}, {self.high_price}, {self.distribution})"

    def sample_price(self) -> Decimal:
        if random.random() <= self.p_regime_refresh or self.prev_price == 0:
            self.prev_price = compute_distribution(
                self.distribution, self.low_price, self.high_price, self.tick_size
            )
            logger.info(
                f"REGIME_REFRESH: symbol={self.symbol}; price={self.prev_price}"
            )
        else:
            price_delta = compute_distribution(
                self.distribution, -self.regime_range, self.regime_range, self.tick_size
            )
            self.prev_price = np.clip(
                self.prev_price + price_delta,
                self.low_price,
                self.high_price,
            )
            logger.info(f"UPDATE: symbol={self.symbol}; price={self.prev_price}")

        return self.prev_price


def create_app(config_root: Path):
    app = Flask(__name__)
    with app.app_context():
        with open(config_root / "price_feed_fuzzer.conf.json") as conf:
            global fuzzers
            fuzzers = {
                c["symbol"]: MarketFuzzer(
                    c["symbol"],
                    Decimal(c["low_price"]),
                    Decimal(c["high_price"]),
                    c["tick_size"],
                    c["distribution"],
                    Decimal(c["p_regime_refresh"]),
                    Decimal(c["regime_range"]),
                )
                for c in json.load(conf)
            }

    @app.route("/price/<symbol>", methods=["GET"])
    def price_feed(symbol):
        global fuzzers
        if symbol in fuzzers:
            body = ComplexOutputEncoder().encode(
                {"price": fuzzers[symbol].sample_price(), "symbol": symbol}
            )
            r = make_response(body)
            r.mimetype = "application/json"
            return r
        else:
            return make_response(f"symbol not found", 404)

    @app.route("/time", methods=["GET"])
    def time_route():
        r = make_response({"time": time.time()})
        r.mimetype = "application/json"
        return r

    return app


config_root = Path(environ.get("CONFIG_DIR", "/opt/dexlabs/bot-config"))
if __name__ == "__main__":
    print(f"Running SSL-enabled server with config root: {config_root}")
    certs_root = Path(environ.get("CERTS_DIR", "/opt/dexlabs/certs"))
    app = create_app(config_root)
    app.run(
        host="0.0.0.0",
        ssl_context=(
            certs_root / "pricefeedfuzzer.crt",
            certs_root / "pricefeedfuzzer.key",
        ),
    )
else:
    print(f"Creating gunicorn app with config root: {config_root}")
    gunicorn_app = create_app(config_root)
