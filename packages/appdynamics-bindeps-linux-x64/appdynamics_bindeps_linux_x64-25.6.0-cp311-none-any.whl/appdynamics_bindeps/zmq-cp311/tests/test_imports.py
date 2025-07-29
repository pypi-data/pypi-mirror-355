"""
Test Imports - the quickest test to ensure that we haven't
introduced version-incompatible syntax errors.
"""
# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

# flake8: noqa: F401

import pytest


def test_toplevel():
    """test toplevel import"""
    import appdynamics_bindeps.zmq as zmq


def test_core():
    """test core imports"""
    from appdynamics_bindeps.zmq import (
        Context,
        Frame,
        Poller,
        Socket,
        constants,
        device,
        proxy,
        pyzmq_version,
        pyzmq_version_info,
        zmq_version,
        zmq_version_info,
    )


def test_devices():
    """test device imports"""
    import appdynamics_bindeps.zmq.devices
    from appdynamics_bindeps.zmq.devices import basedevice, monitoredqueue, monitoredqueuedevice


def test_log():
    """test log imports"""
    import appdynamics_bindeps.zmq.log
    from appdynamics_bindeps.zmq.log import handlers


def test_eventloop():
    """test eventloop imports"""
    pytest.importorskip("tornado")
    import appdynamics_bindeps.zmq.eventloop
    from appdynamics_bindeps.zmq.eventloop import ioloop, zmqstream


def test_utils():
    """test util imports"""
    import appdynamics_bindeps.zmq.utils
    from appdynamics_bindeps.zmq.utils import jsonapi, strtypes


def test_ssh():
    """test ssh imports"""
    from appdynamics_bindeps.zmq.ssh import tunnel


def test_decorators():
    """test decorators imports"""
    from appdynamics_bindeps.zmq.decorators import context, socket


def test_zmq_all():
    import appdynamics_bindeps.zmq as zmq

    for name in zmq.__all__:
        assert hasattr(zmq, name)


@pytest.mark.parametrize("pkgname", ["zmq", "zmq.green"])
@pytest.mark.parametrize(
    "attr",
    [
        "RCVTIMEO",
        "PUSH",
        "zmq_version_info",
        "SocketOption",
        "device",
        "Socket",
        "Context",
    ],
)
def test_all_exports(pkgname, attr):
    import appdynamics_bindeps.zmq as zmq

    subpkg = pytest.importorskip(pkgname)
    for name in zmq.__all__:
        assert hasattr(subpkg, name)

    assert attr in subpkg.__all__
    if attr not in ("Socket", "Context", "device"):
        assert getattr(subpkg, attr) is getattr(zmq, attr)
