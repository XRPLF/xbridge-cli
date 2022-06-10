"""ConfigFile helper class."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Type

_HOME = str(Path.home())

_CONFIG_FOLDER = os.path.join(_HOME, ".config", "sidechain-cli")

_CONFIG_FILE = os.path.join(_CONFIG_FOLDER, "config.json")

# Initialize config file
Path(_CONFIG_FOLDER).mkdir(parents=True, exist_ok=True)
if not os.path.exists(_CONFIG_FILE):
    with open(_CONFIG_FILE, "w") as f:
        data: Dict[str, Any] = {"chains": []}
        json.dump(data, f, indent=4)

# TODO: consider having separate JSONs for each node type
# (e.g. chains.json, witnesses.json)


class ConfigFile:
    """Helper class for working with the config file."""

    def __init__(self: ConfigFile, data: Dict[str, Any]) -> None:
        """
        Initialize a ConfigFile object.

        Args:
            data: The dictionary with the config data.
        """
        self.chains = data["chains"]

    @classmethod
    def from_file(cls: Type[ConfigFile]) -> ConfigFile:
        """
        Initialize a ConfigFile object from a JSON file.

        Returns:
            The ConfigFile object.
        """
        with open(_CONFIG_FILE) as f:
            data = json.load(f)
            return cls(data)

    def to_dict(self: ConfigFile) -> Dict[str, Any]:
        """
        Convert a ConfigFile object back to a dictionary.

        Returns:
            A dictionary representing the data in the object.
        """
        return {"chains": self.chains}

    def write_to_file(self: ConfigFile) -> None:
        """Write the ConfigFile data to file."""
        with open(_CONFIG_FILE, "w") as f:
            json.dump(self.to_dict(), f, indent=4)
