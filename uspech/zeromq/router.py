#!/usr/bin/python3 -tt
# -*- coding: utf-8 -*-

"""
Router Sockets
==============

Simple router for situations when you want to know where messages came from
and where do you want to send them. This should cover most of your IPC needs.

.. code-block:: python
    :caption: Usage example

    from uspech.zeromq.router import Router

    router = Router(default_recipient='example')
    router.connect('tcp://peer.example.com:1234')

    router.send({'question': 'How are you?'})

    async for reply, sender in router:
        print(sender, 'replied:', reply)
        break

.. note::

    Remember that all messages may get lost and never rely on their
    successfull delivery. Always include a timeout & retry mechanism.

    The code in the example above is buggy as the peer might not be so
    readily available, may fail to produce a reply or the reply might get
    delayed and discarded.

Router objects act as an asynchronous iterators producing 2-tuples of the
received message and it's sender.

All outbound messages are JSON encoded and timestamped. Received messages are
JSON decoded and discarded when their timestamp indicates that they are more
than 15 seconds old. Make sure that the peers have their clock synchronized.
"""


from json import loads, dumps
from time import time
from uuid import uuid4

from uspech.zeromq import ctx

import asyncio
import zmq


__all__ = ['Router']


class Router:
    """
    Asynchronous ZeroMQ router wrapper.
    """

    def __init__(self, identity=None, default_recipient=None, loop=None):
        """
        You can supply an identity to be able to bootstrap communication
        by sending messages to well-known participants.  Participants
        sending most messages to a single recipient can set it as default
        and ommit it's name when calling the send method.
        """

        # Get an event loop to use.
        self.loop = loop or asyncio.get_event_loop()

        # Create the 0MQ socket.
        self.socket = ctx.socket(zmq.ROUTER)

        # Hand over socket when peer relocates.
        # This means that we trust peer identities.
        self.socket.setsockopt(zmq.ROUTER_HANDOVER, 1)

        # Assume either user-specified identity or generate our own.
        if identity is not None:
            self.socket.setsockopt_string(zmq.IDENTITY, identity)
        else:
            self.socket.setsockopt_string(zmq.IDENTITY, uuid4().hex)

        # Remember the default recipient.
        self.default_recipient = None
        if default_recipient is not None:
            if not isinstance(default_recipient, bytes):
                self.default_recipient = default_recipient.encode('utf8')
            else:
                self.default_recipient = default_recipient

    def connect(self, address):
        """Connects to ZMQ endpoint."""
        self.socket.connect(address)
        return self

    def bind(self, address):
        """Binds as ZMQ endpoint."""
        self.socket.bind(address)
        return self

    def send(self, message, recipient=None):
        """Send message to specified peer."""

        # If recipient have not been specified, use the default one.
        if recipient is None:
            # But fail if no default have been set.
            if self.default_recipient is None:
                raise TypeError('no recipient specified')

            # Otherwise just use the default and save user some work.
            recipient = self.default_recipient

        else:
            if not isinstance(recipient, bytes):
                recipient = recipient.encode('utf8')

        # JSON-encode the message.
        json = dumps(message).encode('utf8')

        # Get current time as a byte sequence.
        now = str(int(time())).encode('utf8')

        # Send the message.
        self.socket.send_multipart([recipient, json, now])

    def __aiter__(self):
        """This object is an asynchronous iterator."""
        return self

    async def __anext__(self):
        """
        Coroutine producing incoming messages.
        """

        while True:
            sender, data, t = await self.socket.recv_multipart()
            if int(t) + 15 < time():
                continue

            return (loads(data.decode('utf-8')), sender)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    server = Router(identity='server')
    server.bind('tcp://127.0.0.1:4321')

    client = Router(default_recipient='server')
    client.connect('tcp://127.0.0.1:4321')

    async def client_receive():
        async for msg, sender in client:
            print('client received', msg)
            print('stopping loop')
            loop.stop()

    async def server_receive():
        async for msg, sender in server:
            print('server received', msg)
            print('sending reply')
            server.send({'echo': msg}, sender)

    loop.create_task(client_receive())
    loop.create_task(server_receive())

    loop.call_soon(client.send, {'title': 'how are you?'})
    loop.run_forever()


# vim:set sw=4 ts=4 et:
