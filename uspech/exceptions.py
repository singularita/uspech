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

    Exception message may (or rather should) contain parts that have been
    translated to the user's preferred language. Rely only on the additional
    data and the HTTP-compatible error code.
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


# vim:set sw=4 ts=4 et: