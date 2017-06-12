#!/usr/bin/python3 -tt
# -*- coding: utf-8 -*-

"""
Common Site Setup
=================

Collection of modules that allow for site component reuse.

Example:

.. code-block:: python

    from flask import Flask, render_template
    from flask_menu import register_menu
    from flask_babel import _

    from uspech.site.base import setup_base
    from uspech.site.sqlsoup import setup_sqlsoup

    app = Flask(__name__)

    app.config.from_mapping({
        'HOST': '::',
        'PORT': 5000,
        'DEBUG': True,
        'BABEL_DEFAULT_LOCALE': 'en',
        'SQLSOUP_DATABASE_URI': 'postgresql://demo:demo@localhost/demo',
    })

    app.config.from_envvar('DEMO_SETTINGS')

    setup_base(app)
    db = setup_sqlsoup(app)

    @app.route('/')
    @register_menu(app, '.', _('Home'))
    def home():
        foos = db.foo.order_by('id').all()
        return render_template('home.html', foos=foos)
"""


# vim:set sw=4 ts=4 et:
