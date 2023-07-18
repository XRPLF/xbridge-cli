"""Base class for information stored in the CLI."""

from abc import ABC
from typing import Any, Mapping, Type, TypeVar

T = TypeVar("T", bound="ConfigItem")


class ConfigItem(ABC):
    """Abstract class representing a config item."""

    @classmethod
    def from_dict(cls: Type[T], data: Mapping[str, Any]) -> T:
        """
        Convert a dictionary to a given config object.

        Args:
            data: The dictionary to convert.

        Returns:
            The associated config object.
        """
        return cls(**data)
