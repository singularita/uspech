#!/usr/bin/python3 -tt
# -*- coding: utf-8 -*-

"""
Flask-WTForms Extensions
========================
"""


from wtforms import SubmitField


__all__ = ['DeleteField']


class DeleteField(SubmitField):
    """
    Special case of :class:`~wtforms.SubmitField` that is rendered
    differently by our templates.
    """


# vim:set sw=4 ts=4 et:
