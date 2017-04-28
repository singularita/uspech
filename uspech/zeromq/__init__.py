#!/usr/bin/python3 -tt
# -*- coding: utf-8 -*-

import asyncio
import zmq.asyncio
import zmq

ctx = zmq.asyncio.Context()
asyncio.set_event_loop(zmq.asyncio.ZMQEventLoop())

# vim:set sw=4 ts=4 et:
