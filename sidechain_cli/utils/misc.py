"""Miscellaneous util functions."""

import click
from xrpl import CryptoAlgorithm

CryptoAlgorithmChoice = click.Choice([e.value for e in CryptoAlgorithm])
