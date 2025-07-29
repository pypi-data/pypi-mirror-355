import builtins
import logging

import pytest
import verboselogs


def pytest_addoption(parser):
    parser.addoption(
        "--python-only",
        action="store_true",
        help="Forgo communication with the operator and disable verification between reference and operator state. Primarily for prototyping new features.",
    )


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    logging_plugin = config.pluginmanager.get_plugin("logging-plugin")

    logging_plugin.log_cli_handler.formatter.add_color_level(logging.INFO, "cyan")
    logging_plugin.log_cli_handler.formatter.add_color_level(logging.SUCCESS, "green")

    # TODO: Consider a type safe alternative to this approach.
    if config.getoption("--python-only"):
        builtins.PYTHON_ONLY = True
    else:
        builtins.PYTHON_ONLY = False
