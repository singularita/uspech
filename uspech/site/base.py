#!/usr/bin/python3 -tt
# -*- coding: utf-8 -*-

"""
Base Site
=========

Integrates following third-party libraries:

* `Flask-Menu`_ as the menu system.
* `Flask-Babel`_ as the localization system.

.. _Flask-Menu: https://flask-menu.readthedocs.io/en/latest/
.. _Flask-Babel: https://pythonhosted.org/Flask-Babel/

Usage:

.. code-block:: python
    :emphasize-lines: 9

    from flask import Flask, render_template
    from flask_menu import register_menu
    from flask_babel import _

    from uspech.site.base import setup_base

    app = Flask(__name__)

    setup_base(app)

    @app.route('/')
    @register_menu(app, '.', _('Home'))
    def home():
        return render_template('home.html')

.. admonition:: TIP

    Make sure to call ``setup_base`` only after you have registered other
    blueprints. Otherwise you won't be able to override base templates.
"""


from datetime import datetime
from pprint import pformat

from flask import Blueprint, request, render_template, jsonify
from flask_menu import Menu, current_menu
from flask_babel import Babel

from bleach import clean
from markdown import markdown
from humanize import naturalsize
from jinja2 import Markup

from uspech.log import make_logger
from uspech.exceptions import InvalidUsage


__all__ = ['setup_base']


log = make_logger(__name__)
base = Blueprint('base', __name__,
                 static_folder='static',
                 static_url_path='/static/base',
                 template_folder='templates')


@base.app_template_filter('pretty')
def pretty(value):
    return pformat(value, indent=4)


@base.app_template_filter('datetime')
def format_datetime(value):
    if value is not None:
        return value.strftime('%Y-%m-%d %H:%M:%S')


@base.app_template_filter('date')
def format_date(value):
    if value is not None:
        return value.strftime('%Y-%m-%d')


@base.app_template_filter('markdown')
def render_markdown(value):
    if value is not None:
        return Markup(markdown(clean(value), output_format='html5'))


@base.app_template_filter('naturalsize')
def naturalsize_filter(*args, **kwargs):
    return naturalsize(*args, **kwargs)


@base.app_template_global('first_level_menu')
def first_level_menu():
    return current_menu.children


@base.app_template_global('second_level_menu')
def second_level_menu():
    for item in current_menu.children:
        if item.active_item:
            return item.children

    return []


@base.app_template_filter('to_alert')
def category_to_alert(category):
    return {
        'ok': 'alert-success',
        'warning': 'alert-warning',
        'error': 'alert-danger',
    }[category]

@base.app_template_filter('to_icon')
def category_to_icon(category):
    return {
        'ok': 'pficon-ok',
        'warning': 'pficon-warning-triangle-o',
        'error': 'pficon-error-circle-o',
    }[category]


@base.app_errorhandler(InvalidUsage)
def usage_error(exn):
    """
    Treat usage errors differently.
    They are, after all, intended for the end users.
    """

    best = request.accept_mimetypes.best_match([
        'application/json',
        'text/html',
    ])

    if best == 'application/json':
        return jsonify(exn.to_dict()), exn.status

    return render_template('usage.html', error=exn), exn.status


@base.app_errorhandler(Exception)
def system_error(exn):
    """
    Log system errors and return their basic message back to the user.

    This is not ideal as a potential attacker might be able to use this
    information. It should be replaced with a localized generic message.
    """

    log.exception(exn)

    best = request.accept_mimetypes.best_match([
        'application/json',
        'text/html',
    ])

    if best == 'application/json':
        return jsonify(error=str(exn), status=500), 500

    return render_template('error.html', error=exn), 500


@base.app_errorhandler(404)
def not_found(exn):
    """
    Return our customized page instead of the ugly default.
    """

    best = request.accept_mimetypes.best_match([
        'application/json',
        'text/html',
    ])

    if best == 'application/json':
        return jsonify(error=str(exn), status=404), 404

    return render_template('not-found.html', error=exn), 404


def setup_babel(app):
    babel = Babel(app)

    @app.template_global('get_locale')
    @babel.localeselector
    def get_locale():
        if 'lang' in request.args:
            return request.args['lang']

        locale = app.config.get('BABEL_DEFAULT_LOCALE', 'en')
        return request.cookies.get('lang', locale)

    @app.after_request
    def insert_lang_cookie(response):
        """
        Install current language cookie after every request.
        """

        if 'lang' in request.args:
            response.set_cookie('lang', request.args['lang'])

        return response

    return babel


def setup_menu(app):
    return Menu(app)


def setup_base(app):
    """
    Install some generally useful template filters, error handlers,
    menu system and a localization system.

    .. rubric:: Template Filters

    ``pretty``
        Format Python value in a human-readable way.

    ``datetime``
        Format a datetime object using both date and time portions.

    ``date``
        Format a datetime object using only the date portion.

    ``to_alert``
        Convert strings ``ok``, ``warning`` and ``error`` to alert classes.

    ``to_icon``
        Convert strings ``ok``, ``warning`` and ``error`` to icon names.

    .. rubric:: Exception Handlers

    ``InvalidUsage``
        Handler that presents the error to the user.

    ``Exception``
        Default handler the hides the details from the user but logs the
        traceback instead.

    .. rubric:: Error Handlers

    ``404``
        Custom handler for HTTP 404 Not Found statuses that presents the
        situation to the user in a friendly way.

    .. rubric:: Templates

    You can use the templates that come with this blueprint in your
    application or other blueprints. You can also override these templates
    if you include them in your applications's templates folder.

    ``base.html``
        Base page container that includes PatternFly from a CDN (with SRI
        hashes to prevent malicious code injection in modern browsers).

    ``usage.html``
        Page to describe the :class:`~uspech.exceptions.InvalidUsage`
        exceptions that reach the web interface.

    ``error.html``
        Page to apologize for other exceptions.

    ``not-found.html``
        Page to explain that a resource was not found.
    """

    setup_menu(app)
    setup_babel(app)

    app.register_blueprint(base)


# vim:set sw=4 ts=4 et:
