"""Sidechain CLI Exceptions."""

from __future__ import annotations

from click import ClickException


class SidechainCLIException(ClickException):
    """Base sidechain CLI exception."""

    pass


class AttestationTimeoutException(SidechainCLIException):
    """Exception thrown if there is a timeout when waiting for attestations."""

    def __init__(self: AttestationTimeoutException) -> None:
        """Initialize AttestationTimeoutException."""
        super().__init__("Timeout on attestations.")
