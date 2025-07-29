from collections.abc import Iterable

from ddx.common.logging import assert_logger
from tests.python_only import maybe_match

logger = assert_logger(__name__)


def assert_tx_eq(expected, actual):
    """
    Assert that the expected and actual transactions are equal.
    """

    if not isinstance(expected, Iterable):
        expected = [expected]
    expected = [v for v in expected if v]
    if actual is None:
        actual = [None for _ in expected]
    logger.debug(f"expected list: {expected}")
    logger.debug(f"actual list: {actual}")
    assert len(expected) == len(actual)
    for expected_tx, actual_tx in zip(expected, actual):
        maybe_match(logger, expected_tx, actual_tx)
    return expected if expected else None
