import logging
import random
from typing import Dict, Optional
from aiohttp import ClientSession
from attrs import define, field
from ddx.common.utils import (
    to_base_unit_amount_list,
    ComplexOutputEncoder,
)
from eth_abi.utils.padding import zpad32_right
from eth_account.signers.local import LocalAccount
from web3.auto import w3
from zero_ex.contract_wrappers import TxParams

from ddx._rust.common import ProductSymbol
from ddx._rust.common.enums import OrderSide, OrderType
from ddx._rust.common.requests.intents import (
    CancelAllIntent,
    OrderIntent,
    ProfileUpdateIntent,
    WithdrawIntent,
)
from ddx._rust.common.state.keys import StrategyKey
from ddx._rust.decimal import Decimal

from ddx.rest_client.contracts.collateral import Collateral
from ddx.rest_client.contracts.collateral_k_y_c import CollateralKYC
from ddx.derivadex_client import DerivaDEXClient
from ddx.rest_client.utils.encryption_utils import encrypt_with_nonce
from utils.utils import round_to_unit

logger = logging.getLogger(__name__)


@define
class Strategy:
    """
    Defines a Strategy

    A Strategy contains information pertaining to a trader's
    cross-margined strategy, such as their free and frozen collaterals
    and max leverage.

    Attributes:
        strategy_id (str): Identifier for strategy
        avail_collateral (Dict[str, Decimal]): collateral address <> collateral value indicating the collateral available for trading
        locked_collateral (Dict[str, Decimal]): collateral address <> collateral value indicating the collateral available for on-chain withdrawal
        max_leverage (int): Max leverage the strategy can take
        frozen (bool): Whether the strategy is frozen or not (relevant for tokenization)
    """

    strategy_id: str = field(eq=str.lower)
    avail_collateral: Dict[str, Decimal]
    locked_collateral: Dict[str, Decimal]
    max_leverage: int
    frozen: bool


async def update_profile(
    derivadex_client: DerivaDEXClient,
    client,
    web3_account: LocalAccount,
):
    """
    Update profile to pay fees in DDX.

    Parameters
    ----------
    derivadex_client : DerivaDEXClient
        DerivaDEX client wrapper
    web3_account : str
        Address
    """

    # Initialize a ProfileUpdateIntent
    profile_update_intent = ProfileUpdateIntent(
        f"0x{derivadex_client.get_encoded_nonce()}",
        True,
    )
    profile_update_msg = f"PROFILE_UPDATE: address={web3_account.address}; updating profile to pay fees in DDX"

    # Prepare request to operator
    profile_update_intent.signature = web3_account.signHash(
        profile_update_intent.hash_eip712(
            (derivadex_client.chain_id, derivadex_client.verifying_contract)
        )
    ).signature.hex()

    # Encrypt request
    encrypted_contents = encrypt_with_nonce(
        derivadex_client.encryption_key,
        ComplexOutputEncoder().encode(profile_update_intent.json),
    )

    # Submit profile update request
    response = await client.post(
        f"{derivadex_client.webserver_url}/v2/request",
        data=encrypted_contents,
    )

    try:
        response_json = await response.json()
        logging.info(f"(SUCCESS) {profile_update_msg}: {response_json}")
        return response_json
    except:
        logging.info(f"(FAILURE) {profile_update_msg}: {response}")
        return None


async def deposit_for_account(
    derivadex_client: DerivaDEXClient,
    client: ClientSession,
    collateral_address: str,
    strategy: str,
    deposit_amount: Decimal,
    private_key: str,
    initial_nonce: Optional[int] = None,
    consider_profile_update=False,
):
    web3_account = derivadex_client.w3.eth.account.from_key(private_key)
    kyc_authorization_response = await client.get(
        f"{derivadex_client.webserver_url}/kyc/v1/kyc-auth?trader={web3_account.address}"
    )
    kyc_authorization_json = await kyc_authorization_response.json()

    # Deposit
    collateral_contract = CollateralKYC(
        derivadex_client.w3, derivadex_client.verifying_contract
    )
    built_tx = collateral_contract.deposit.build_transaction(
        collateral_address,
        zpad32_right(
            len(strategy).to_bytes(1, byteorder="little") + strategy.encode("utf8")
        ),
        int(deposit_amount * Decimal("1e6")),
        kyc_authorization_json["kycAuth"]["expiryBlock"],
        kyc_authorization_json["signature"],
        tx_params=TxParams(
            from_=web3_account.address,
            nonce=(
                initial_nonce
                if initial_nonce is not None
                else derivadex_client.w3.eth.get_transaction_count(web3_account.address)
            ),
        ),
    )
    signed_tx = derivadex_client.w3.eth.account.sign_transaction(
        built_tx, private_key=private_key
    )
    derivadex_client.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    logging.info(f"Deposited {web3_account.address} ")

    if consider_profile_update and bool(random.getrandbits(1)):
        await update_profile(
            derivadex_client,
            client,
            web3_account,
        )

        logging.info(f"Updated profile {web3_account.address}")


async def withdraw_for_account(
    derivadex_client: DerivaDEXClient,
    client,
    collateral_address: str,
    private_key: str,
    strategy: str,
    checkpointed_epoch_id: int,
    initial_nonce: Optional[int] = None,
):
    collateral_address = w3.to_checksum_address(collateral_address)

    address = derivadex_client.w3.eth.account.from_key(private_key).address
    strategy_key = StrategyKey(
        f"0x00{address[2:]}",
        StrategyKey.generate_strategy_id_hash(strategy),
    )

    params = {"key": str(strategy_key.encode_key()), "epochId": checkpointed_epoch_id}
    response = await client.get(
        f"{derivadex_client.webserver_url}/v2/proof",
        params=params,
    )
    response_json = await response.json()

    checkpointed_strategy = {
        "strategyId": zpad32_right(
            len(strategy).to_bytes(1, byteorder="little") + strategy.encode("utf8")
        ),
        "maxLeverage": 3,
        "frozen": False,
        "availCollateral": {
            "tokens": [collateral_address],
            "amounts": to_base_unit_amount_list(
                [
                    Decimal(val)
                    for val in list(
                        response_json["item"]["Strategy"]["availCollateral"].values()
                    )
                ],
                6,
            ),
        },
        "lockedCollateral": {
            "tokens": [collateral_address],
            "amounts": to_base_unit_amount_list(
                [
                    Decimal(val)
                    for val in list(
                        response_json["item"]["Strategy"]["lockedCollateral"].values()
                    )
                ],
                6,
            ),
        },
    }

    withdrawal_amount = int(
        random.uniform(
            0,
            2 * float(checkpointed_strategy["lockedCollateral"]["amounts"][0]),
        )
    )

    strategy_proof = f'0x{bytes(response_json["proof"]).hex()}'
    withdraw_data = {
        "tokens": [collateral_address],
        "amounts": [withdrawal_amount],
    }

    # Withdraw
    collateral_contract = Collateral(
        derivadex_client.w3, derivadex_client.verifying_contract
    )

    built_tx = collateral_contract.withdraw.build_transaction(
        StrategyKey.generate_strategy_id_hash(strategy),
        withdraw_data,
        checkpointed_strategy,
        strategy_proof,
        tx_params=TxParams(
            from_=address,
            nonce=(
                initial_nonce
                if initial_nonce is not None
                else derivadex_client.w3.eth.get_transaction_count(address)
            ),
        ),
    )
    signed_tx = derivadex_client.w3.eth.account.sign_transaction(
        built_tx, private_key=private_key
    )
    derivadex_client.w3.eth.send_raw_transaction(signed_tx.rawTransaction)


async def place_order(
    derivadex_client: DerivaDEXClient,
    client,
    web3_account: LocalAccount,
    strategy: str,
    symbol: ProductSymbol,
    long_likelihood: Decimal,
    quantity: Decimal,
    base_px: Decimal,
):
    """
    Place new orders around a base price

    Parameters
    ----------
    derivadex_client : DerivaDEXClient
        DerivaDEX client wrapper
    web3_account : str
        Address
    symbol : str
        Market symbol
    long_likelihood : Decimal
        Specifies the likelihood of going long [0=never, 1=always]
    quantity : Decimal
        Size to submit
    base_px : Decimal
        Price to quote around (if limit)
    """

    # Choose a random side based on the account's long likelihood
    side = OrderSide.Bid if random.random() < long_likelihood else OrderSide.Ask

    # Choose a random quantity
    quantity = round_to_unit(
        Decimal(str(random.uniform(0.1, float(quantity * Decimal("2"))))),
        1,
    )

    if bool(random.getrandbits(1)):
        order_type = OrderType.Limit
        price = round_to_unit(
            (
                Decimal(str(random.uniform(0, float(base_px))))
                if side == OrderSide.Bid
                else Decimal(str(random.uniform(float(base_px), 2 * float(base_px))))
            ),
            1 if symbol == "ETHP" else 0,
        )
    else:
        order_type = OrderType.Market
        price = Decimal("0")

    # Initialize a market OrderIntent
    order_intent = OrderIntent(
        symbol,
        strategy,
        side,
        order_type,
        f"0x{derivadex_client.get_encoded_nonce()}",
        quantity,
        price,
        Decimal("0"),
        None,
    )
    place_order_msg = f"PLACE_ORDER: address={web3_account.address}; symbol={symbol}; order_type={order_type}; side={order_intent.side}; amount={order_intent.amount}; price={price}"

    # Prepare request to operator
    order_intent.signature = web3_account.signHash(
        order_intent.hash_eip712(
            (derivadex_client.chain_id, derivadex_client.verifying_contract)
        )
    ).signature.hex()

    # Encrypt request
    encrypted_contents = encrypt_with_nonce(
        derivadex_client.encryption_key,
        ComplexOutputEncoder().encode(order_intent.json),
    )

    # Submit order request
    response = await client.post(
        f"{derivadex_client.webserver_url}/v2/request",
        data=encrypted_contents,
    )

    try:
        response_json = await response.json()
        logging.info(f"(SUCCESS) {place_order_msg}: {response_json}")
        return response_json
    except:
        logging.info(f"(FAILURE) {place_order_msg}: {response}")
        return None


async def cancel_all(
    derivadex_client: DerivaDEXClient,
    client,
    web3_account: LocalAccount,
    strategy: str,
    symbol: ProductSymbol,
):
    """
    Place new orders around a base price

    Parameters
    ----------
    derivadex_client : DerivaDEXClient
        DerivaDEX client wrapper
    web3_account : str
        Address
    strategy : str
        Strategy Id
    symbol : str
        Market symbol
    """

    cancel_all_intent = CancelAllIntent(
        symbol,
        strategy,
        f"0x{derivadex_client.get_encoded_nonce()}",
        None,
    )

    cancel_all_msg = f"CANCEL_ALL: address={web3_account.address}"

    # Prepare request to operator
    cancel_all_intent.signature = web3_account.signHash(
        cancel_all_intent.hash_eip712(
            (derivadex_client.chain_id, derivadex_client.verifying_contract)
        )
    ).signature.hex()

    # Encrypt request
    encrypted_contents = encrypt_with_nonce(
        derivadex_client.encryption_key,
        ComplexOutputEncoder().encode(cancel_all_intent.json),
    )

    # Submit order request
    response = await client.post(
        f"{derivadex_client.webserver_url}/v2/request",
        data=encrypted_contents,
    )

    try:
        response_json = await response.json()
        logging.info(f"(SUCCESS) {cancel_all_msg}: {response_json}")
        return response_json
    except:
        logging.info(f"(FAILURE) {cancel_all_msg}: {response}")
        return None


async def signal_withdrawal(
    derivadex_client: DerivaDEXClient,
    client,
    web3_account: LocalAccount,
    collateral_address: str,
    strategy: str,
    amount: Decimal,
):
    """
    Signal withdrawal

    Parameters
    ----------
    derivadex_client : DerivaDEXClient
        DerivaDEX client wrapper
    web3_account : str
        Address
    collateral_address : str
        Collateral address
    amount : Decimal
        Amount
    """

    # Initialize a WithdrawIntent
    withdraw_intent = WithdrawIntent(
        strategy,
        collateral_address,
        amount,
        f"0x{derivadex_client.get_encoded_nonce()}",
    )
    signal_withdrawal_msg = (
        f"WITHDRAW ({web3_account.address}): withdrawing ({withdraw_intent.amount})"
    )

    # Prepare request to operator
    withdraw_intent.signature = web3_account.signHash(
        withdraw_intent.hash_eip712(
            (derivadex_client.chain_id, derivadex_client.verifying_contract)
        )
    ).signature.hex()

    # Encrypt request
    encrypted_contents = encrypt_with_nonce(
        derivadex_client.encryption_key,
        ComplexOutputEncoder().encode(withdraw_intent.json),
    )

    # Submit withdraw request
    response = await client.post(
        f"{derivadex_client.webserver_url}/v2/request",
        data=encrypted_contents,
    )

    try:
        response_json = await response.json()
        logging.info(f"(SUCCESS) {signal_withdrawal_msg}: {response_json}")
        return response_json
    except:
        logging.info(f"(FAILURE) {signal_withdrawal_msg}: {response}")
        return None


async def get_strategy(
    derivadex_client: DerivaDEXClient,
    collateral_address: str,
    trader_address: str,
    strategy_str: str,
):
    strategy = await derivadex_client.get_strategy(
        f"0x{trader_address[2:]}", strategy_str
    )
    logging.info(f"Strategy: {strategy}")
    if strategy is not None and "value" in strategy:
        return Strategy(
            strategy["value"]["strategyId"],
            {
                collateral_address: Decimal(
                    strategy["value"]["availCollateral"],
                )
            },
            {
                collateral_address: Decimal(
                    strategy["value"]["lockedCollateral"],
                )
            },
            int(strategy["value"]["maxLeverage"]),
            strategy["value"]["frozen"],
        )
    elif strategy is not None:
        return Strategy(
            strategy_str,
            {},
            {},
            3,
            False,
        )
    return None


def sign_send_wait_tx(w3, tx, private_key):
    signed_txn = w3.eth.account.sign_transaction(
        tx,
        private_key=private_key,
    )
    try:
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        logger.info(f"waiting for tx {tx_hash.hex()}")
        w3.eth.wait_for_transaction_receipt(tx_hash)
        logger.info(f"tx {tx_hash.hex()} found on chain")
    except:
        logging.warn("Failed to send / sign wait tx")
