"""
The wntr.network.controls module includes methods to define network controls
and control actions.  These controls modify parameters in the network during
simulation.
"""

import math
import enum
import numpy as np
import logging
import six
from wntr.network.controls import ControlBase, ControlCondition
from wntr.network.elements import LinkStatus
import abc
from wntr.utils.ordered_set import OrderedSet
from collections import OrderedDict
from wntr.network.elements import Tank, Junction, Valve, Pump, Reservoir, Pipe, Link
from wntr.utils.doc_inheritor import DocInheritor
import warnings
from typing import Hashable, Dict, Any, Tuple, MutableSet, Iterable

logger = logging.getLogger(__name__)


class _ControlType(enum.Enum):
    presolve = 0
    postsolve = 1
    rule = 2
    pre_and_postsolve = 3
    feasibility = 4  # controls necessary to ensure the problem being solved is feasible
    stop_condition = 5  # non-EPANET controls for manually indicated breakpoints in an EPANET run.


@DocInheritor({"is_control_action_required", "run_control_action", "requires", "actions"})
class StopControl(ControlBase):
    """
    Subset of a Rule, but no actions are executed.
    """

    def __init__(self, condition, name=None):
        """
        Parameters
        ----------
        condition: ControlCondition
            The condition that should be used to determine when the actions need to be activated. When the condition
            evaluates to True, then the simulation stops.
        name: str
            The name of the control
        """
        self.update_condition(condition)
        self._which = None
        self._name = name
        if self._name is None:
            self._name = ""
        self._control_type = _ControlType.stop_condition

    def to_dict(self):
        ret = dict()
        if self._control_type == _ControlType.stop_condition:
            ret["type"] = "stop_condition"
            ret["name"] = str(self._name)
            ret["condition"] = str(self._condition)
        return ret

    @property
    def epanet_control_type(self):
        """
        The control type. Note that presolve and postsolve controls are both simple controls in Epanet.

        Returns
        -------
        control_type: _ControlType
        """
        return self._control_type

    def _shift(self, step):
        return self._condition._shift(step)

    def requires(self):
        req = self._condition.requires()
        return req

    def actions(self):
        return []

    @property
    def name(self):
        """
        A string representation of the Control.
        """
        if self._name is not None:
            return self._name
        else:
            return "/".join(str(self).split())

    def __repr__(self):
        fmt = "<StopCondition: '{}', {}>"
        return fmt.format(
            self._name,
            repr(self._condition),
        )

    def __str__(self):
        text = "IF {}".format(str(self._condition))
        then_text = " THEN STOP PRIORITY 100"
        return text + then_text

    def is_control_action_required(self):
        do = self._condition.evaluate()
        if do:
            self._which = "then"
            return True, None
        else:
            self._which = None
            return False, None

    def run_control_action(self):
        if self._which == "then":
            pass
        else:
            raise RuntimeError("control actions called even though if-then statement was False")

    def update_condition(self, condition: ControlCondition):
        """Update the controls condition in place

        Parameters
        ----------
        condition : ControlCondition
            The new condition for this control to use

        Raises
        ------
        ValueError
            If the provided condition isn't a valid ControlCondition
        """
        try:
            logger.info(f"Replacing {self._condition} with {condition}")
        except AttributeError:
            # Occurs during intialisation
            pass
        if not isinstance(condition, ControlCondition):
            raise ValueError("The conditions argument must be a ControlCondition instance")
        self._condition = condition


class StopCriteria(object):
    def __init__(self):
        self._controls = dict()
        """OrderedSet of ControlBase"""

    def __iter__(self):
        return iter(self._controls)

    def register_criterion(self, control):
        """
        Register a control with the ControlManager

        Parameters
        ----------
        control: ControlBase
        """
        if not isinstance(control, StopControl):
            raise ValueError("Criteria must be a StopControl")
        self._controls[control.name] = control

    def deregister(self, name_or_control):
        """
        Deregister a control with the ControlManager

        Parameters
        ----------
        control: ControlBase
        """
        if isinstance(name_or_control, str):
            self._controls.pop(name_or_control)
        elif isinstance(name_or_control, StopControl):
            self._controls.pop(name_or_control.name)
        else:
            raise ValueError("name_or_control must be a string or StopControl")

    def check(self):
        """
        Check which controls have actions that need activated.

        Returns
        -------
        conditions_active: list of tuple
            The tuple is (ControlBase, backtrack)
        """
        conditions_active = []
        for n, c in self._controls.items():
            do, back = c.is_control_action_required()
            if do:
                conditions_active.append(
                    (
                        n,
                        c,
                    )
                )
        return conditions_active

    def requires(self):
        """
        Check what nodes/links are required for execution.

        Returns
        -------
        OrderedSet
            The elements that are needed to execute the conditions.
        """
        _requires = OrderedSet()
        for n, c in self._controls.items():
            _requires.update(c.requires())
        return _requires
