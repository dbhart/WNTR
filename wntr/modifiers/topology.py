"""
Topology modifier classes.
"""

import numpy as _np
import wntr.modifiers as _mods
import wntr.network as _net
import logging as _logging

_logger = _logging.getLogger(__name__)

class PipeClosures(_mods.NetworkModifier):
    """Close some subset of pipes within the network.

    Close pipes based on a list, a stochastic subset of a list, or stochastic subset
    of all pipes. A maximum diameter can also be specified.

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

