"""Util methods for the sidechain CLI."""

from sidechain_cli.utils.config_file import CONFIG_FOLDER
from sidechain_cli.utils.config_utils import (
    add_chain,
    add_witness,
    check_chain_exists,
    check_witness_exists,
    get_config,
    remove_chain,
    remove_witness,
)
from sidechain_cli.utils.types import ChainData, WitnessData

__all__ = [
    "add_chain",
    "add_witness",
    "check_chain_exists",
    "check_witness_exists",
    "get_config",
    "remove_chain",
    "remove_witness",
    "ChainData",
    "WitnessData",
    "CONFIG_FOLDER",
]
