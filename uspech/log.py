#!/usr/bin/python3 -tt
# -*- coding: utf-8 -*-

import logging

from logging import debug, info, warning, error, critical, exception
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL


__all__ = ['debug', 'info', 'warning', 'error', 'critical', 'exception',
           'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL',
           'make_logger', 'handler', 'log_to_console']


handler = None


def make_logger(name):
    """
    Create new logger with a null handler.

    Useful shortcut for libraries that want to use their own logger.
    For example:

    .. code-block:: python

        log = make_logger('dice')

        def roll(sides):
            log.debug('Preparing to roll an %i-sided die...', sides)
            result = randint(1, sides)

            log.info('Roll result: %i/%i' % (result, sides))
            return result
    """

    logger = logging.getLogger(name)
    logger.addHandler(logging.NullHandler())
    return logger


def log_to_console(level=None):
    """
    Install a root logging handler that will output to console.

    Log messages of given level or higher will be produced to the console
    formatted to include their level, source name and the actual message.
    There will be no timestamps in the output since we assume ``systemd``
    will be used for long-running services that might need them.
    """

    import os
    global handler

    if handler is not None:
        logging.root.removeHandler(handler)
        handler = None

    if level is None:
        level = os.environ.get('LOGLEVEL')
        if level in ('debug', 'info', 'warning', 'error', 'critical'):
            level = getattr(logging, level.upper())
        else:
            level = INFO

    fmt = logging.Formatter('%(levelname)s: [%(name)s] %(message)s')

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(fmt)
    logging.root.addHandler(handler)
    logging.root.setLevel(level)


# vim:set sw=4 ts=4 et:
