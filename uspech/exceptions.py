#!/usr/bin/python3 -tt
# -*- coding: utf-8 -*-

"""
Exceptions
==========
"""


class InvalidUsage(Exception):
    """
    User has requested that we perform an invalid or illegal operation.

    The operation was refused and this eception needs to be propagated
    back to the user to inform his about the situation. The exception
    should not get swallowed along the way.
    """

    data = {}
    """Mapping with additional data."""

    status = 400
    """HTTP-compatible error code."""

    def __init__(self, message, data=None, status=None):
        super().__init__(message)

        self.data = data or {}
        self.status = status or 400

    def to_dict(self):
        """
        Convert the exception to a dictionary.

        This method is useful when the exception needs to be JSON-encoded.
        Make sure that the :attr:`data` can be serialized at least in this
        manner -- users depend on that.
        """

        return {
            'status': self.status,
            'error': str(self),
            'data': self.data,
        }


class RemoteError(InvalidUsage):
    """
    An operation that attempted to use a different service as instructed by
    the user has failed. User needs to be informed.
    """


# vim:set sw=4 ts=4 et:
