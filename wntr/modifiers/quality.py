"""
Initial water quality modifier classes.
"""

import numpy as _np
from . import base as _mods
import wntr.network as _net
import logging as _logging

_logger = _logging.getLogger(__name__)

class SetInitialQuality(_mods.NetworkModifier):
    """
    Set the initial quality based on results from a previous simulation.
    """
    _file_fmt = 'pickle'

    def __init__(self, results=None, time=None, idx=None, filename=None, file_fmt=None):
        self._results = results
        self._time = time
        self._idx = idx
        self._filename = filename
        if file_fmt is not None:
            self._file_fmt = file_fmt

    def configure(self, results=None, time=None, idx=None, filename=None, file_fmt=None):
        if results is not None:
            self._results = results
        if time is not None:
            self._time = time
        if idx is not None:
            self._idx = idx
        if filename is not None:
            self._filename = filename
        if file_fmt is not None:
            self._file_fmt = file_fmt

    def apply(self, wnm):
        pass

