import asyncio
import simplejson as json

from ddx._rust.decimal import Decimal

from ddx.auditor.auditor_driver import AuditorDriver
from ddx.common.epoch_params import EpochParams
from ddx.common.trade_mining_params import TradeMiningParams
from utils.utils import get_config, exchange_is_up


if __name__ == "__main__":
    config_json = get_config("auditor")

    if not exchange_is_up(
        config_json["webserver_url"], config_json["contract_deployment"]
    ):
        raise RuntimeError(f"exchange at {config_json['webserver_url']} is not up")

    epoch_params = EpochParams(
        config_json["epoch_params"]["epoch_size"],
        config_json["epoch_params"]["price_checkpoint_size"],
        config_json["epoch_params"]["settlement_epoch_length"],
        config_json["epoch_params"]["pnl_realization_period"],
        config_json["epoch_params"]["funding_period"],
        config_json["epoch_params"]["trade_mining_period"],
        config_json["epoch_params"]["expiry_price_leaves_duration"],
    )
    trade_mining_params = TradeMiningParams(
        config_json["trade_mining_params"]["trade_mining_length"],
        (Decimal("35_000_000") / (10 * 365 * 3)).recorded_amount(),
        Decimal("0.2"),
    )
    auditor_driver = AuditorDriver(
        config_json["webserver_url"],
        (
            json.loads(config_json["genesis_params"])
            if "genesis_params" in config_json
            else None
        ),
        epoch_params,
        trade_mining_params,
        json.loads(config_json["collateral_tranches"]),
        config_json["contract_deployment"],
    )

    asyncio.run(auditor_driver.main())
