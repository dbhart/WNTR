"""
Demand modifier classes.
"""

import numpy as _np
import wntr.modifiers as _mods
import wntr.network as _net
import logging as _logging

_logger = _logging.getLogger(__name__)

class UniquePatterns(_mods.NetworkModifier):
    """Create unique demand multiplier patterns for each junction.

    Each pattern assigned to a junction is copied, and the new pattern applied
    to that junction. Options including splitting (into equal sizes) pattern steps
    to change to pattern step size (for example, from 1hr to 30min pattern steps).
    If step size is changed, the multiplier value is kept the same for each of the
    split steps.

    Patterns can also be extended by repeating out to the duration of the simulation.
    New patterns are given a name ``pat_prefix + junction.name``. Remember to ensure
    the name length will not exceed maximum lengths if using EPANET.

    Parameters
    ----------
    new_step : int or False
        New time step size for patterns. Default of False (or 0) means no change
        in step size.
    repeat_pats : bool
        Repeat patterns out to the duration of the simulation. Default of False.
    pattern_prefix : str
        String added to begining of new pattern names. Default of "p-".


    """

    def __init__(self, new_step=False, repeat_pats=False, pattern_prefix='p-'):
        self._new_step = new_step
        self._rep_pats = repeat_pats
        self._prefix = pattern_prefix

    def configure(self, new_step=None, repeat_pats=None, pattern_prefix=None):
        """(Re)configure the UniquePatterns modifier model.

        Parameters
        ----------
        new_step : int or False
            If int or False, then change the setting of new_step. If omitted (or None), do
            not change from previous setting.
        repeat_pats : bool
            If True or False, then change the setting. If omitted (or None), do not change
            from previous setting.
        pattern_prefix : str
            Change the pattern prefix to a new string. If omitted (or None), do not change
            from previous setting.

        """
        if new_step is not None:
            self._new_step = new_step
        if repeat_pats is not None:
            self._rep_pats = repeat_pats
        if pattern_prefix is not None:
            self._prefix = pattern_prefix

    def apply(self, wnm):
        """Apply the UniquePatterns network modifier to a water network model.

        Parameters
        ----------
        wnm : WaterNetworkModel
            The water network model to be modified.

        """
        self._convert_to_per_node_patterns(wnm)
        if self._new_step:
            self._pattern_to_new_timestep(wnm, self._new_step)
        if self._rep_pats:
            self._make_patterns_same_length(wnm)


    def _convert_to_per_node_patterns(self, wnm):
        """
        Convert from general patterns to per-node patterns.
        """
        #t0pnd = time.time()
        for n in wnm.nodes(_net.Junction):
            node = n[1]
            if node.base_demand != 0.0:
                node_name = node.name()
                pattern_name = node.demand_pattern_name
                if pattern_name is None:
                    continue
                pattern_value = _np.asarray(wnm.get_pattern(pattern_name))
                new_demand_values = pattern_value
                new_pattern_name = self._prefix + node_name
                wnm.add_pattern(new_pattern_name, new_demand_values)
                node.demand_pattern_name = new_pattern_name

    def _pattern_to_new_timestep(self, wnm, dt):
        """
        Modify patterns to use a finer pattern size.

        This function modifies patterns only, not base/nodal demands.

        Note
        ----
        This function **does not** perform any interpolation. As an example, a
        network with a 1 hour pattern timestep and 30 minute hydraulic timestep
        with simple pattern `[ 3, 8, 1, 9]` would become
        `[3, 3, 8, 8, 1, 1, 9, 9]`.

        Parameters
        ----------
        network : wntr.network.WaterNetworkModel
            The water network model created from an EPANET-2 .inp file.

        """
        pat_ts = wnm.options.pattern_timestep
        hyd_ts = dt
        n_rep = pat_ts / hyd_ts
        wnm.options.pattern_timestep = int(hyd_ts)
        try:
            for pat in wnm._patterns:
                pat_vals = wnm.get_pattern(pat)
                new_vals = _np.zeros(len(pat_vals)*n_rep)
                for j in range(len(new_vals)):
                    i = int(j/n_rep)
                    new_vals[j] = pat_vals[i]
                wnm.add_pattern(pat,new_vals)
        except TypeError as e:
            _logger.error('Pattern timesteps cannot be equally divided by new timestep')
            raise e
        return len(new_vals)

    def _make_patterns_same_length(self, wnm):
        num_steps = int(wnm.options.duration / wnm.options.pattern_timestep)
        for name in wnm._patterns.keys():
            vals = wnm.get_pattern(name)
            n_pat_step = len(vals)
            new_pat_values = _np.zeros(num_steps)
            for i in range(num_steps):
                new_pat_values[i] = vals[i%n_pat_step]
            wnm.add_pattern(name, new_pat_values)
        _logger.info("Total pattern steps now %d",num_steps)
