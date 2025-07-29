from os import environ
from pathlib import Path
import configargparse
import requests
import simplejson as json

from ddx._rust.decimal import Decimal


def round_to_unit(val: Decimal, tick_size: int) -> Decimal:
    return val.quantize(tick_size)


def make_contract_server_url(webserver_url: str) -> str:
    return f"{webserver_url.replace('https','http',1)}/contract-server/addresses"


def get_config(service_name: str):
    config_root = Path(environ["CONFIG_DIR"])
    service_id = environ.get("SERVICE_ID", None)
    file_name = (
        f"{service_name}-{int(service_id)}" if service_id is not None else service_name
    )
    p = configargparse.ArgParser()
    p.add_argument(
        "-d",
        "--config-dir",
        default=str(config_root),
        help=f"Directory containing the {file_name}.conf.json configuration file (default: {config_root}))",
    )
    p.add_argument(
        "-c",
        "--config",
        help=f"Raw config string override for the {file_name} service. If provided, this will override the config file inferred from the config dir and service id",
    )

    options = p.parse_args()

    print(options)
    print("----------")
    print(p.format_help())
    print("----------")
    print(p.format_values())

    if options.config:
        return json.loads(options.config)
    with open(Path(options.config_dir) / f"{file_name}.conf.json", "r") as fp:
        return json.load(fp)


def get_contract_deployment_info(
    webserver_url: str, contract_deployment: str, contract_server_url: str = None
):
    if contract_server_url:
        r = requests.get(
            contract_server_url, params={"contractDeployment": contract_deployment}
        )
    else:
        r = requests.get(
            make_contract_server_url(webserver_url),
            params={"contractDeployment": contract_deployment},
        )
    return r.json()


def exchange_is_up(webserver_url: str, contract_deployment: str) -> bool:
    session = retrying_session()

    contract_server_is_up = session.get(
        make_contract_server_url(webserver_url),
        params={"contractDeployment": contract_deployment},
    ).ok

    return contract_server_is_up and operator_is_up(webserver_url)


def auditor_is_up(auditor_host: str) -> bool:
    session = retrying_session()
    # Q: http or https?
    return session.get(f"http://{auditor_host}:8766/trader").ok


def operator_is_up(webserver_url: str) -> bool:
    session = retrying_session()
    return session.get(f"{webserver_url}/v2/status").ok


def retrying_session(total=10, backoff_factor=1):
    session = requests.Session()
    retries = requests.adapters.Retry(
        total=total,
        backoff_factor=backoff_factor,
        status_forcelist=[404, 429, 500, 502, 503, 504],
    )
    adapter = requests.adapters.HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session
