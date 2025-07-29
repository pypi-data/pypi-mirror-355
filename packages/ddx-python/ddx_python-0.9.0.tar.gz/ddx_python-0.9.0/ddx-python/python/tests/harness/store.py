"""
Store module.
"""

import copy
import datetime
import functools
import inspect
import json
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional
from aiohttp import ClientSession
from dotenv import load_dotenv
from hexbytes import HexBytes
from typing_extensions import Self
from web3 import Web3
from web3._utils.rpc_abi import RPC

from ddx._rust.common import OperatorContext, ProductSymbol, get_operator_context
from ddx._rust.common.enums import PositionSide
from ddx._rust.common.requests import Block
from ddx._rust.common.specs import SpecsKind
from ddx._rust.common.state import DerivadexSMT
from ddx._rust.common.state.keys import PositionKey, StrategyKey
from ddx._rust.decimal import Decimal
from ddx._rust.h256 import H256

from ddx.common.epoch_params import EpochParams
from ddx.common.logging import auditor_logger, local_logger
from ddx.common.market_specs import MarketSpecs
from ddx.common.trade_mining_params import TradeMiningParams
from ddx.common.utils import get_parsed_tx_log_entry
from ddx.auditor.auditor_driver import AuditorDriver
from tests.harness.execution.state import State
from tests.harness.market_aware_account import MarketAwareAccount
from tests.harness.market_data_driver.market_data_driver import MarketDataDriver
from tests.harness.market_data_driver.tick import Tick
from tests.harness.wallet import Wallet


logger = logging.getLogger(__name__)
l_logger = local_logger(__name__)
a_logger = auditor_logger(__name__)
load_dotenv()
GENESIS_PARAMS = json.loads(os.getenv("GENESIS_PARAMS"))


class Store:
    """
    Data access bridge than generates and hold requests to mirror the local state transitions.

    This exposes a function trading API for intuitive data generation. Internally, it transitions the local
    State (e.g. post an order to the book), and computes the business rules to generate the array
    of operator requests needed to mirror the state transition.

    Provided correct execution logic on both sides, this component is responsible for keeping the state roots in sync.


    ### Execution environment

    The only supported mode of execution is inside a container in the docker network as defaults suggest.
    """

    @asynccontextmanager
    async def run_scenario(
        self,
        market_data_driver: MarketDataDriver,
        client: ClientSession,
        scenario: Optional[str] = None,
        rpc_url: str = "http://ethereum:8545",
        mnemonic: str = "concert load couple harbor equip island argue ramp clarify fence smart topic",
        # TODO: Do the same or equivalent for other arguments.
        operator_url: str = os.environ.get(
            "OPERATOR_SIM_URL", "http://operator-sim:8090/v2/sim"
        ),
        contract_server_url: str = "http://contract-server:4040/addresses",
        contract_deployment: str = "snapshot",
        genesis_params: dict = GENESIS_PARAMS,
        collateral_tranches: list[tuple[Decimal, Decimal]] = [
            (Decimal("1_000"), Decimal("10_000")),
            (Decimal("1_000_000"), Decimal("1_000_000")),
            (Decimal("0"), Decimal("100_000_000")),
        ],
        epoch_size: int = 10,
        price_checkpoint_size: int = 20,
        settlement_epoch_multiplier: int = 6,
        pnl_realization_settlement_multiplier: int = 2,
        funding_settlement_multiplier: int = 1,
        trade_mining_settlement_multiplier: int = 1,
        trade_mining_length: int = 3,
        expiry_price_leaves_duration: int = 20,
        version_db: list[str] = [],
    ):
        try:
            self.market_data_driver = market_data_driver
            self.time_value = 0
            self.timestamp = self.market_data_driver.start_timestamp
            start_timestamp = (
                int(self.timestamp.timestamp() * 1000)
                + self.timestamp.microsecond // 1000
            )
            self.epoch_id = 1
            self.settlement_epoch_id = 1

            # Initialize web3 service
            self.w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 60}))

            # Emulates the local verified state where business logic is executed
            self.wallet = Wallet(mnemonic)

            self.client = client
            self.operator_url = operator_url
            self.contract_server_url = contract_server_url
            self.contract_deployment = contract_deployment

            context: OperatorContext = get_operator_context()
            self.verifying_contract_address = context.contract_address
            self.chain_id = context.chain_id

            self.market_specs = MarketSpecs(genesis_params)

            settlement_epoch_length = settlement_epoch_multiplier * epoch_size
            self.epoch_params = EpochParams(
                epoch_size,
                price_checkpoint_size,
                settlement_epoch_length,
                pnl_realization_settlement_multiplier * settlement_epoch_length,
                funding_settlement_multiplier * settlement_epoch_length,
                trade_mining_settlement_multiplier * settlement_epoch_length,
                expiry_price_leaves_duration,
            )
            self.trade_mining_params = TradeMiningParams(
                trade_mining_length,
                (Decimal("35_000_000") / (10 * 365 * 3)).recorded_amount(),
                Decimal("0.2"),
            )
            logger.info(
                f"Parameters:\n\tEpoch: {self.epoch_params}\n\tTrade Mining: {self.trade_mining_params}"
            )

            # auditor-driven state
            self.auditor_driver = AuditorDriver(
                "",
                genesis_params,
                self.epoch_params,
                self.trade_mining_params,
                collateral_tranches,
                contract_deployment,
            )
            self.auditor_driver._reset()
            genesis_tx_log_event = get_parsed_tx_log_entry(
                {
                    "epochId": 0,
                    "ordinal": 0,
                    "stateRootHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
                    "requestIndex": 0,
                    "batchId": 0,
                    "time": {
                        "value": 0,
                        "timestamp": start_timestamp,
                    },
                    "event": {
                        "t": "EpochMarker",
                        "c": {
                            "kind": "Genesis",
                        },
                    },
                }
            )
            self.auditor_driver.process_tx_log_event(genesis_tx_log_event, True)[0]

            assert {
                item[0]: item[1].as_product_specs(item[0].kind)
                for item in self.auditor_driver.smt.all_specs()
                if item[0].kind
                in [SpecsKind.SingleNamePerpetual, SpecsKind.QuarterlyExpiryFuture]
            } == self.market_specs.market_specs, "Expected operator-determined market specs to match reference-impl-determined market specs"

            # reference-impl-driven state
            self.state = State(
                copy.deepcopy(self.auditor_driver.smt),
                genesis_params,
                self.market_specs,
                self.epoch_params,
                self.trade_mining_params,
                collateral_tranches,
            )

            if scenario is None:
                # If no scenario is specified, use the current test function name.
                scenario = inspect.stack()[2].function
            # Setup test scenario.
            signer_address = None
            release_hash = None
            json = {
                "op": "Setup",
                "scenario": scenario,
                "startTimestamp": start_timestamp,
                "versionDb": version_db,
                "genesisParams": genesis_params,
                "tradeMiningLength": self.trade_mining_params.trade_mining_length,
                "fundingPriceLeavesDuration": self.epoch_params.funding_period,
                "expiryPriceLeavesDuration": self.epoch_params.expiry_price_leaves_duration,
            }
            async with self.client.post(
                self.operator_url,
                json=json,
            ) as response:
                response = await response.json()
                logger.info(f"Setup response with identity: {response}")
                signer_address = response["ok"]["signerAddress"]
                release_hash = response["ok"]["releaseHash"]

            # Get a handle on the async tick generator.
            tick_generator = self.market_data_driver.ticks()

            # Advance one tick.
            await anext(tick_generator)

            # Register the simulated operator's signer to the local state
            self.state.register_signer(release_hash, signer_address)

            yield tick_generator
        finally:
            # Force close the tick generator.
            await tick_generator.aclose()

            # Tear down the test scenario.
            await self.client.post(
                self.operator_url,
                json={"op": "Teardown"},
            )

    def is_trade_mining(self):
        return (
            self.settlement_epoch_id < self.trade_mining_params.trade_mining_length + 1
        )

    async def advance(self, tick_generator: AsyncIterator[Tick], number: int):
        """
        Advance the state by a number of ticks.
        """
        for _ in range(number):
            yield await anext(tick_generator)
        logger.info(f"Advanced {number} ticks")

    async def advance_until_time(
        self, tick_generator: AsyncIterator[Tick], time: datetime.datetime
    ):
        """
        Advance the state until the next wall clock time. Note: always increments at least once.
        """
        while True:
            yield await anext(tick_generator)

            if self.timestamp >= time:
                break

    async def _advance_until_next_tick_cmd(
        self, tick_generator: AsyncIterator[Tick], cmd_tick_length: int
    ):
        """
        Advance the state until the next tick cmd. Note: always increments at least once.
        """
        while True:
            yield await anext(tick_generator)

            if self.time_value > 1 and (self.time_value - 1) % cmd_tick_length == 0:
                break

    async def advance_until_next_epoch(self, tick_generator: AsyncIterator[Tick]):
        async for tick in self._advance_until_next_tick_cmd(
            tick_generator, self.epoch_params.epoch_size
        ):
            yield tick

    async def advance_until_next_price_checkpoint(
        self, tick_generator: AsyncIterator[Tick]
    ):
        async for tick in self._advance_until_next_tick_cmd(
            tick_generator, self.epoch_params.price_checkpoint_size
        ):
            yield tick

    async def advance_until_next_funding_period(
        self, tick_generator: AsyncIterator[Tick]
    ):
        async for tick in self._advance_until_next_tick_cmd(
            tick_generator, self.epoch_params.funding_period
        ):
            yield tick

    async def advance_until_next_pnl_realization_period(
        self, tick_generator: AsyncIterator[Tick]
    ):
        async for tick in self._advance_until_next_tick_cmd(
            tick_generator, self.epoch_params.pnl_realization_period
        ):
            yield tick

    async def advance_until_next_trade_mining_period(
        self, tick_generator: AsyncIterator[Tick]
    ):
        async for tick in self._advance_until_next_tick_cmd(
            tick_generator, self.epoch_params.trade_mining_period
        ):
            yield tick

    async def advance_until_price(
        self,
        tick_generator: AsyncIterator[Tick],
        symbol: ProductSymbol,
        side: PositionSide,
        price: Decimal,
    ):
        side = 1 if side == PositionSide.Long else -1
        while True:
            tick = await anext(tick_generator)
            yield tick

            if symbol not in tick.prices:
                continue
            tick_price = tick.prices[symbol]

            logger.info(
                f"looking for current price: {tick_price} {'<=' if side == 1 else '>='} target price: {price}; currently {side * tick_price <= side * price}"
            )
            if side * tick_price <= side * price:
                break

    async def advance_until_liquidation_price(
        self,
        tick_generator: AsyncIterator[Tick],
        position_key: PositionKey,
    ):
        """
        Advance the state until the liquidation price is the current index price. Note: always increments at least once.
        """

        def liquidation_price(position, price, total_value, mmf):
            side = Decimal("1") if position.side == PositionSide.Long else Decimal("-1")
            return (total_value - position.balance * price.mark_price * side) / (
                position.balance * (mmf - side)
            )

        strategy_key = StrategyKey(
            position_key.trader_address,
            position_key.strategy_id_hash,
        )
        market_aware_account = MarketAwareAccount(
            self.state.smt.strategy(strategy_key),
            self.state.positions_for_strategy(strategy_key),
        )
        liquidated_position, price = market_aware_account.positions[position_key.symbol]
        liquidation_price = liquidation_price(
            liquidated_position,
            price,
            market_aware_account.total_value,
            market_aware_account.maintenance_margin_fraction,
        )
        logger.info(f"advancing until liquidation price {liquidation_price} is met")
        async for tick in self.advance_until_price(
            tick_generator,
            position_key.symbol,
            liquidated_position.side,
            liquidation_price,
        ):
            yield tick

    @classmethod
    @functools.cache
    def the_store(cls) -> Self:
        return cls()

    async def send_and_audit_request(
        self, request, local_items: Optional[tuple[DerivadexSMT, H256]] = None
    ):
        logger.debug(f"request json: {request.json}")
        response = await self.client.put(
            f"{self.operator_url}/1",
            json=[request.json],
        )
        if response.status != 200:
            raise RuntimeError(f"operator error: {(await response.json())['err']}")
        response = await response.json()
        logger.debug(f"response: {response}")

        # set starting tree for this request to be the local tree state to isolate this request's processing
        # and make the auditor effectively stateless between requests when using the test harness
        if local_items is not None:
            self.auditor_driver.smt = local_items[0]
        if txs := response["txs"]:
            tx_log_events, maybe_checkpoints = zip(*txs)
            logger.debug(f"tx_log_events: {tx_log_events}")
            logger.debug(f"maybe_checkpoints: {maybe_checkpoints}")
            txs = []
            for parsed_tx_log_event in (
                get_parsed_tx_log_entry(tx_log_event) for tx_log_event in tx_log_events
            ):
                txs.extend(
                    self.auditor_driver.process_tx_log_event(parsed_tx_log_event, True)
                )
            logger.debug(f"processed txs: {txs}")
            # Parse checkpoint metadata if any
            for checkpoint in maybe_checkpoints:
                if checkpoint is not None:
                    logger.debug(f"processing checkpoint: {checkpoint}")
                    self.state.last_created_checkpoint = checkpoint

        auditor_root = H256.from_bytes(
            bytes.fromhex(
                self.auditor_driver.current_state_root_hash.removeprefix("0x")
            )
        )
        if local_items is not None and (local_root := local_items[1]) != auditor_root:
            l_logger.error(
                f"smt leaves after request {txs[0].request_index}: {[(str(key), value.abi_encoded_value().hex()) for key, value in self.state.smt.all_leaves()]}\n\nHuman readable:\n{str(self.state.smt.all_leaves())}"
            )
            a_logger.error(
                f"smt leaves after request {txs[0].request_index}: {[(str(key), value.abi_encoded_value().hex()) for key, value in self.auditor_driver.smt.all_leaves()]}\n\nHuman readable:\n{str(self.auditor_driver.smt.all_leaves())}"
            )

            raise RuntimeError(
                f"local reference state root hash {local_root} != current state root hash {auditor_root}"
            )

        return txs

    async def send_and_confirm_eth_tx(
        self,
        raw_transaction: HexBytes,
        confirmed_blocks: int,
        send_operator_requests: bool = True,
    ):
        import tests.python_only

        next_block_number = self.w3.eth.block_number + 1
        tx_hash = None
        for i in range(confirmed_blocks + 1):
            if i == 0:
                tx_hash = self.w3.eth.send_raw_transaction(raw_transaction).hex()
            else:
                self.w3.manager.request_blocking(RPC.evm_mine, [])
            if send_operator_requests:
                block = Block(next_block_number + i)
                await self.send_and_audit_request(block)

        return tx_hash
