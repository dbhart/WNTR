"""
Package for network modifier models.

For example, define models that modify hydraulics stochastically,
or which modify water chemistry parameters, or change initial
conditions.
"""

from .base import NetworkModifier
from .demands import UniquePatterns
from .topology import PipeClosures