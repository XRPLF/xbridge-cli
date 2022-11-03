"""Witness information stored in the CLI."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, cast

from sidechain_cli.utils.config_file.server_config import ServerConfig


@dataclass
class WitnessConfig(ServerConfig):
    """Object representing the config for a witness."""

    @property
    def witnessd(self: WitnessConfig) -> str:
        """
        Get the witnessd executable. Alias for `self.exe`.

        Returns:
            `self.exe`.
        """
        return self.exe

    def get_config(self: WitnessConfig) -> Dict[str, Any]:
        """
        Get the config file for this witness.

        Returns:
            The JSON dictionary for this config file.
        """
        with open(self.config) as f:
            return cast(Dict[str, Any], json.load(f))
