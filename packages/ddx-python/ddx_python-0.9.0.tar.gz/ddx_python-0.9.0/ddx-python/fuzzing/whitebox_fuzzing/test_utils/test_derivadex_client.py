"""
TestDerivaDEX Client
"""
from typing import Optional

from ddx.derivadex_client import DerivaDEXClient
from whitebox_fuzzing.test_utils.test_kyc_resource import TestKYCResource
from whitebox_fuzzing.test_utils.test_on_chain_resource import TestOnChainResource


class TestDerivaDEXClient(DerivaDEXClient):
    """
    Test-enabled DerivaDEX client with additional testing functionality.
    Extends the standard client with test-only operations.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._test_kyc: Optional[TestKYCResource] = None
        self._on_chain: Optional[TestOnChainResource] = None

    @property
    def kyc(self) -> TestKYCResource:
        """Access test KYC operations."""

        if self._test_kyc is None:
            self._test_kyc = TestKYCResource(self._http, self._base_url)

        return self._test_kyc

    @property
    def on_chain(self) -> TestOnChainResource:
        """
        Access on-chain operations.
        Overrides base client to provide test functionality.
        """

        if self._on_chain is None:
            self._on_chain = TestOnChainResource(
                self._http,
                self._base_url,
                self.web3_account,
                self.w3,
                self._verifying_contract,
            )

        return self._on_chain
