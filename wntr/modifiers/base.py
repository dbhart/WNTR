"""
Abstract Base Class for NetworkModifier based models.
"""

from abc import ABCMeta, abstractmethod
import numpy as np

import logging, warnings
logger = logging.getLogger(__name__)


class NetworkModifier(object):
    __metaclass__ = ABCMeta

    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def configure(self, **kwargs):
        return NotImplemented

    @abstractmethod
    def apply(self, wnm):
        return NotImplemented

