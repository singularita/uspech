#!/usr/bin/python3 -tt
# -*- coding: utf-8 -*-

"""
SQLSoup Integration
===================
"""


from sqlsoup import SQLSoup
from sqlalchemy import Table, Column

from uspech.log import make_logger


__all__ = ['setup_sqlsoup']


log = make_logger(__name__)


def setup_sqlsoup(app, view_keys={}):
    """
    Register SQLSoup with a Flask application.

    Expects following Flask configuration options:

    ``SQLSOUP_DATABASE_URI = 'sqlite:///:memory:'``
        Database URI to connect to.

    ``SQLSOUP_ROLLBACK_ON_TEARDOWN = True``
        Flag that controls automatic rollback after every request.

    :param app: The Flask application to augment.
    :param view_keys: Mapping of database view names to lists of primary keys
        needed for SQLSoup to be able to access these views as normal tables.
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

    for name, keys in view_keys.items():
        columns = [Column(key, primary_key=True) for key in keys]
        table = Table(name, app.sqlsoup._metadata, *columns, autoload=True)
        app.sqlsoup.map_to(name, selectable=table)

    return app.sqlsoup


# vim:set sw=4 ts=4 et:
