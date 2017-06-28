#!/usr/bin/python3 -tt
# -*- coding: utf-8 -*-

"""
Pagination
==========

Mostly automatic pagination over medium-sized tables that is good enough for
most sites dealing with data entered manually by users.

.. admonition:: NOTE

    Do not use for large collections of automatically acquired entries.
    Linear performance of offset-based database seeking will be very slow.

Example:

.. code-block:: python

    from uspech.site.pagination import Page
    from demo.site import db

    page = Page(db.user.order_by('login'), count=25)
    return render_template('users.html', page=page)

You can use the ``pagination.html`` template to render the navigation.
"""

from math import ceil

from flask import request
from flask_babel import _

from uspech.exceptions import InvalidUsage


__all__ = ['Page']


class Page:
    """
    Page is automatically initialized using :attr:`flask.request.args` and
    the supplied query base that is counted and sliced. Like this:

    .. code-block:: python

        items = query.offset(offset).limit(size).all()
        items_total = query.count()

    You need to make sure that the ordering of the query results stays stable.
    Ideally include something like ``.order_by('id')`` or any other key.

    All page and item offsets are base 1 for user convenience.
    """

    size = 20
    """Current page size."""

    items = []
    """Items on the current page."""

    items_total = 100
    """Total count of the items in the result set."""

    items_first = 1
    """Offset of the first item on the current page."""

    items_last = 50
    """Offset of the last item on the current page."""

    number = 1
    """Current page number."""

    first = 1
    """First page number."""

    last = 2
    """Last page number."""

    next = 2
    """Following page number (or current if on the first page)."""

    prev = 1
    """Previous page number (or current if on the last page)."""


    def __init__(self, query, size=20):
        assert size > 0, 'Page size must be positive'

        self.size = size

        try:
            self.number = int(request.args.get('page', '1'))
        except ValueError:
            raise InvalidUsage(_('Invalid page argument (wrong type)'))

        if self.number < 1:
            raise InvalidUsage(_('Invalid page argument (< 1)'))

        offset = (self.number - 1) * size

        self.items_total = query.count()
        self.items_first = offset + 1

        self.items = query.offset(offset).limit(size).all()
        self.items_last = offset + len(self.items)

        self.first = 1
        self.last = max(1, ceil(self.items_total / size))

        self.next = min(self.number + 1, self.last)
        self.prev = max(self.number - 1, self.first)

    def is_first(self):
        return self.number == self.first

    def is_last(self):
        return self.number == self.last


# vim:set sw=4 ts=4 et:
