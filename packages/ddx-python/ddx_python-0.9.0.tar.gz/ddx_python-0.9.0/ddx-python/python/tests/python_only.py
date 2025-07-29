import builtins
import inspect
import logging
import os
import re
from functools import partial
from typing import TYPE_CHECKING, Iterable, Optional

import pytest
from aioresponses import aioresponses
from ddx._rust.common.state import DerivadexSMT
from ddx._rust.h256 import H256
from tests.harness.store import Store

# TODO: Review this approach: https://gitlab.com/dexlabs/derivadex/-/merge_requests/3187#note_2526337716
python_only = getattr(builtins, "PYTHON_ONLY", False)

# DEPLOYMENT_INFO = {
#     "addresses": {
#         "ddxAddress": "0x1dc4c1cefef38a777b15aa20260a54e584b16c48",
#         "ddxWalletCloneableAddress": "0xb7c9b454221e26880eb9c3101b3295ca7d8279ef",
#         "derivaDEXAddress": "0x1d7022f5b17d2f8b695918fb48fa1089c9f85401",
#         "diFundTokenFactoryAddress": "0x6000eca38b8b5bba64986182fe2a69c57f6b5414",
#         "governanceAddress": "0x871dd7c2b4b25e1aa18728e9d5f2af4c4e431f5c",
#         "insuranceFundAddress": "0x8726c7414ac023d23348326b47af3205185fd035",
#         "pauseAddress": "0x4112f5fc3f737e813ca8cc1a48d1da3dc8719435",
#         "traderAddress": "0xaa86dda78e9434aca114b6676fc742a18d15a1cc",
#         "usdtAddress": "0x0b1ba0af832d7c05fd64161e0db78e85978e8082",
#         "ausdtAddress": "0x34d402f14d58e001d8efbe6585051bf9706aa064",
#         "cusdtAddress": "0x48bacb9266a570d521063ef5dd96e61686dbe788",
#         "usdcAddress": "0xb69e673309512a9d726f87304c6984054f87a93b",
#         "ausdcAddress": "0xdc688d29394a3f1e6f1e5100862776691afaf3d2",
#         "cusdcAddress": "0xe86bb98fcf9bff3512c74589b78fb168200cc546",
#         "husdAddress": "0x0000000000000000000000000000000000000000",
#         "gusdAddress": "0x3BB5e799f186032F7c2F6D80055c6cB7d22Bb3Ee",
#         "gnosisSafeAddress": "0xaE32496491b53841efb51829d6f886387708F99B",
#         "gnosisSafeProxyFactoryAddress": "0x50e55Af101C777bA7A1d560a774A82eF002ced9F",
#         "createCallAddress": "0x8538FcBccba7f5303d2C679Fa5d7A629A8c9bf4A",
#         "gnosisSafeProxyAddress": "0xBDf662e4A4F4b01Ab0c06A13f2Bb9DEB13bb5cFC",
#         "bannerAddress": "0x32eecaf51dfea9618e9bc94e9fbfddb1bbdcba15",
#         "fundedInsuranceFundAddress": "0x04b5dadd2c0d6a261bfafbc964e0cac48585def3",
#         "registrationAddress": "0x8ea76477cfaca8f7ea06477fd3c09a740ac6012a",
#         "checkpointAddress": "0x8d42e38980ce74736c21c059b2240df09958d3c8",
#         "specsAddress": "0x6346e3a22d2ef8fee3b3c2171367490e52d81c52",
#         "collateralAddress": "0x4d3d5c850dd5bd9d6f4adda3dd039a3c8054ca29",
#         "stakeAddress": "0xa31e64ea55b9b6bbb9d6a676738e9a5b23149f84",
#         "custodianAddress": "0x7e3f4e1deb8d3a05d9d2da87d9521268d0ec3239",
#         "rejectAddress": "0x7bf7bb74c43dc141293aff12a2d7de350e9b09e0",
#     },
#     "chainId": 1337,
# }

MOCK_SETUP_RESPONSE = {
    "ok": {
        "releaseHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "signerAddress": "0x000000000000000000000000000000000000000000",
    }
}


@pytest.fixture(autouse=True)
def maybe_mock_client():
    if python_only:
        with aioresponses() as mocked:
            operator_regex = re.compile(r"^http://[^/]+/v2/sim$")
            mocked.post(
                operator_regex,
                payload=MOCK_SETUP_RESPONSE,
                repeat=True,
            )
            yield
    else:
        yield


def send_wrapper(func):
    async def maybe_send_and_audit_request(
        self, request, local_items: Optional[tuple[DerivadexSMT, H256]] = None
    ):
        return await func(self, request, local_items) if not python_only else None

    return maybe_send_and_audit_request


Store.send_and_audit_request = send_wrapper(Store.send_and_audit_request)


def freeze_logging(func):
    """Decorator to set the logging pathname, filename, and lineno based on the caller of the decorated function."""

    class CustomLogRecord(logging.LogRecord):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Capture the stack frame of the caller outside the current module and not from __init__.py
            for f in inspect.stack():
                if (
                    f[1] != inspect.getfile(inspect.currentframe())
                    and "__init__.py" not in f[1]
                    and "utils.py" not in f[1]
                ):
                    self.pathname = f[1]
                    self.filename = f[1].split("/")[-1]
                    self.lineno = f[2]
                    break
            else:
                self.pathname = "unknown_path"
                self.lineno = 0

    def wrapper(*args, **kwargs):
        # Temporarily replace the LogRecord class for the logger
        original_factory = logging.getLogRecordFactory()
        logging.setLogRecordFactory(CustomLogRecord)

        try:
            return func(*args, **kwargs)
        finally:
            # Restore the original LogRecord class
            logging.setLogRecordFactory(original_factory)

    return wrapper


@freeze_logging
def maybe_match(logger, expected, actual):
    if not python_only:
        assert type(expected).__name__ == type(actual).__name__
    tx_type_name = type(expected).__name__
    logger.info(
        f"{tx_type_name}:\n\tactual: {actual if not python_only else 'N/A'}\n\texpected: {expected}"
    )
    if not python_only:
        assert actual == expected
