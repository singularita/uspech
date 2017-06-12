#!/usr/bin/python3 -tt
# -*- coding: utf-8 -*-

"""
SQLSoup Integration
===================
"""


from sqlsoup import SQLSoup
from uspech.log import make_logger


__all__ = ['setup_sqlsoup']


log = make_logger(__name__)


def setup_sqlsoup(app):
    """
    Register SQLSoup with a Flask application.

    Expects following Flask configuration options:

    ``SQLSOUP_DATABASE_URI = 'sqlite:///:memory:'``
        Database URI to connect to.

    ``SQLSOUP_ROLLBACK_ON_TEARDOWN = True``
        Flag that controls automatic rollback after every request.
    """

    app.config.setdefault('SQLSOUP_DATABASE_URI', 'sqlite:///:memory:')
    app.config.setdefault('SQLSOUP_ROLLBACK_ON_TEARDOWN', True)

    app.sqlsoup = SQLSoup(app.config['SQLSOUP_DATABASE_URI'])

    if app.config['SQLSOUP_ROLLBACK_ON_TEARDOWN']:
        @app.teardown_request
        def teardown_request(exn=None):
            try:
                app.sqlsoup.session.rollback()
            except Exception as subexn:
                # Teardown callbacks may not raise exceptions.
                log.exception(subexn)

    return app.sqlsoup


# vim:set sw=4 ts=4 et:
