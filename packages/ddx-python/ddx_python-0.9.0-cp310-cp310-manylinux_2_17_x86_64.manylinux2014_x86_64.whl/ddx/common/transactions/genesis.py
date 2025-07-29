"""
Genesis module
"""

from typing import Optional

from attrs import define, field
from ddx.common.logging import auditor_logger
from ddx.common.transactions.event import Event
from ddx._rust.common.specs import SpecsKind
from ddx._rust.common.state import Balance, DerivadexSMT
from ddx._rust.common.state.keys import InsuranceFundKey, SpecsKey
from ddx._rust.decimal import Decimal

logger = auditor_logger(__name__)


@define
class Genesis(Event):
    """
    Defines a Genesis

    A Genesis is a non-transitioning transaction that indicates
    the start of the first epoch.

    Attributes:
        state_root_hash (str): State root hash at time of marker
        request_index (int): Sequenced request index of transaction
    """

    state_root_hash: Optional[str] = field(eq=str.lower)
    request_index: int = field(default=-1, eq=False)

    @classmethod
    def decode_value_into_cls(cls, raw_tx_log_event: dict):
        """
        Decode a raw transaction log event (dict) into a Genesis
        instance.

        Parameters
        ----------
        raw_tx_log_event : dict
            Raw transaction log event being processed
        """

        genesis_tx_event = raw_tx_log_event["event"]["c"]

        return cls(
            genesis_tx_event.get("stateRootHash"),
            raw_tx_log_event["requestIndex"],
        )

    def process_tx(
        self,
        **kwargs,
    ):
        """
        Process an EpochMarker transaction of type Genesis. This
        indicates the very first event in the transaction log, although
        it is not state-transitioning in the way typical transactions
        are.

        Parameters
        ----------
        **kwargs
            Additional args specific to Genesis transactions
        """

        if (
            collaterals := kwargs["genesis_params"]["Genesis"].get("insuranceFundCap")
        ) is not None:
            insurance_fund_balance = Balance.new_from_many(collaterals)
        else:
            insurance_fund_balance = Balance.default()

        ddx_fee_pool = kwargs["genesis_params"]["Genesis"].get("ddxFeePool")
        if ddx_fee_pool is None:
            ddx_fee_pool = Decimal("0")

        specs = {}
        for key, val in kwargs["genesis_params"]["Genesis"]["specs"].items():
            if key.startswith("SINGLENAMEPERP"):
                kind = SpecsKind.SingleNamePerpetual
            elif key.startswith("INDEXFUNDPERP"):
                kind = SpecsKind.IndexFundPerpetual
            elif key.startswith("QUARTERLYEXPIRYFUTURE"):
                kind = SpecsKind.QuarterlyExpiryFuture
            elif key.startswith("GATEWAY"):
                kind = SpecsKind.MarketGateway
            else:
                raise Exception("Invalid spec in Genesis params")

            specs[SpecsKey(kind, key.split("-")[1])] = val

        logger.info(
            f"Initializing SMT from genesis:\n\tInsurance fund: {insurance_fund_balance}\n\tDDX fee pool: {ddx_fee_pool}\n\tSpecs: {specs}\n\tCurrent datetime: {kwargs['current_time']}"
        )
        smt = DerivadexSMT.from_genesis(
            insurance_fund_balance, ddx_fee_pool, specs, kwargs["current_time"]
        )
        kwargs["smt"](kwargs["auditor_instance"], smt)

        # Set the expected epoch ID to be 1 and the expected tx ordinal
        # to be -1, because we immediately increment this by 1, thus
        # setting it to 0, which will be the first tx ordinal of the
        # next epoch
        kwargs["expected_epoch_id"](kwargs["auditor_instance"], 1)
        kwargs["expected_tx_ordinal"](kwargs["auditor_instance"], -1)
