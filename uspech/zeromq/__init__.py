#!/usr/bin/python3 -tt
# -*- coding: utf-8 -*-

"""
ZeroMQ
======

Common ZeroMQ patterns that work with asyncio infrastructure.

.. warning::

    Importing this module (or any sub module) will install a ZeroMQ compatible
    event loop, so make sure to do it before you spawn any tasks on the default
    loop. As fair as I know, it is not possible to use the ZeroMQ with other
    loops, so no GNOME + ZeroMQ on asyncio.
"""


import asyncio
import zmq.asyncio
import zmq

ctx = zmq.asyncio.Context()
asyncio.set_event_loop(zmq.asyncio.ZMQEventLoop())


# vim:set sw=4 ts=4 et:
