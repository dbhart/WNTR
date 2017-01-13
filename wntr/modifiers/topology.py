"""
Topology modifier classes.
"""

import numpy as _np
from . import base as _mods
import wntr.network as _net
import logging as _logging

_logger = _logging.getLogger(__name__)

class PipeClosures(_mods.NetworkModifier):
    """Close some subset of pipes within the network.

    Close pipes based on a list, a stochastic subset of a list, or stochastic subset
    of all pipes. A minumum and/or maximum diameter of pipe to be closed can also be
    specified.

    Parameters
    ----------
    pipe_list : list
        A list of pipe labels to limit the possible pipes that can be closed.
    stochastic_fraction : float
        A threshold value for a random variable :math:`X \sim U(0,1)` where a pipe is
        closed if :math:`X` is less than the threshold.
        If this value is False or 0.0, then all otherwise selected pipes will be closed.
    min_diameter : float
        A minimum diameter for pipes that can be closed.
    max_diameter : float
        A maximum diameter for pipes that can be closed.


    .. warning::

        If no values are provided at all, every pipe in the system would be closed.


    """
    def __init__(self, pipe_list=None, stochastic_fraction=False,
                 min_diameter=False, max_diameter=False):
        self._fraction = stochastic_fraction
        self._pipelist = pipe_list
        self._mindiam = min_diameter
        self._maxdiam = max_diameter

    def configure(self, pipe_list=None, stochastic_fraction=None,
                  min_diameter=None, max_diameter=None):
        if stochastic_fraction is not None:
            self._fraction = stochastic_fraction
        if pipe_list is not None:
            self._pipelist = pipe_list
        if min_diameter is not None:
            self._mindiam = min_diameter
        if max_diameter is not None:
            self._maxdiam = max_diameter

    def apply(self, wnm):
        ct = 0
        pipes_closed = []
        if self._pipelist:
            pipes = set(self._pipelist)
        else:
            pipes = set(wnm._pipes.keys())
        if self._maxdiam > 0.0:
            dpipes = wnm.query_link_attribute('diameter', operation=_np.less_equal,
                                              value=self._maxdiam,
                                              link_type=_net.Pipe).keys()
            pipes = pipes.intersection(dpipes)
        if self._mindiam > 0.0:
            dpipes = wnm.query_link_attribute('diameter', operation=_np.greater_equal,
                                              value=self._mindiam,
                                              link_type=_net.Pipe).keys()
            pipes = pipes.intersection(dpipes)
        for label in pipes:
            pipe = wnm.get_link(label)
            if (not self._fraction) or (_np.random.rand() < self._fraction):
                pipe._base_status = 0
                pipes_closed.append(label)
                ct += 1
        if self._fraction > 0.0 and ct == 0:
            return self._stoch_close_pipes(wnm)
        _logger.debug('Modified %d pipes to status CLOSED', ct)

