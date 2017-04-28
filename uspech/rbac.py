#!/usr/bin/python3 -tt
# -*- coding: utf-8 -*-

from fnmatch import fnmatch

import re


__all__ = ['AccessModel']


class AccessModel:
    """
    Access model with privilege rules.

    The rules specify what groups or roles must be an user member of
    in oder to obtain certain privileges. The privileges are not
    hierarchical, meaning that ``admin`` does not have to be an ``user``.
    If the application needs some privileges to overlap, it should repeat
    the patterns in both rules.

    For example:

    .. code-block:: python

        [
            ('user', ['+*', '-impotent']),
            ('admin', ['+Public\\Domain Administrators']),
            ('operator', ['+Public/Domain+Administrators']),
        ]

    All backslashes in the rules are normalized to forward slashes and
    spaces are replaced with plus signs.

    If a single privilege gets mentioned several times, it is requivalent
    to it being specified just once with all the patterns concatenated.
    """

    def __init__(self, items):
        self.patterns = []

        for priv, pats in items:
            for pat in pats:
                pat = pat.strip().replace('\\', '/').replace(' ', '+')

                if not fnmatch(pat, '[+-]*'):
                    raise ValueError('invalid pattern: %r' % (pat,))

                self.patterns.append((pat, priv))

    def privileges(self, role):
        """
        Resolve a role to a set of application specific privileges.
        """

        privs = set()

        for pat, priv in self.patterns:
            if fnmatch(pat, '+*') and fnmatch(role, pat[1:]):
                privs.add(priv)
            elif fnmatch(pat, '-*') and fnmatch(role, pat[1:]):
                privs.discard(priv)

        return privs

    def have_privilege(self, priv, roles):
        """
        Determine whether specified roles have given privilege.
        """

        for role in roles or ['impotent']:
            if priv in self.privileges(role):
                return True

        return False


# vim:set sw=4 ts=4 et:
