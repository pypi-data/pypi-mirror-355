"""pure-Python sugar wrappers for core 0MQ objects."""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.


from appdynamics_bindeps.zmq import error
from appdynamics_bindeps.zmq.sugar import context, frame, poll, socket, tracker, version

__all__ = []
for submod in (context, error, frame, poll, socket, tracker, version):
    __all__.extend(submod.__all__)

from appdynamics_bindeps.zmq.error import *  # noqa
from appdynamics_bindeps.zmq.sugar.context import *  # noqa
from appdynamics_bindeps.zmq.sugar.frame import *  # noqa
from appdynamics_bindeps.zmq.sugar.poll import *  # noqa
from appdynamics_bindeps.zmq.sugar.socket import *  # noqa

# deprecated:
from appdynamics_bindeps.zmq.sugar.stopwatch import Stopwatch  # noqa
from appdynamics_bindeps.zmq.sugar.tracker import *  # noqa
from appdynamics_bindeps.zmq.sugar.version import *  # noqa

__all__.append('Stopwatch')
