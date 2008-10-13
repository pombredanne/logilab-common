# -*- coding: utf-8 -*-

"""Extends the logging module from the standard library.

:copyright: 2000-2008 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
:contact: http://www.logilab.fr/ -- mailto:contact@logilab.fr
:license: General Public License version 2 - http://www.gnu.org/licenses
"""
__docformat__ = "restructuredtext en"

import logging

from logilab.common.textutils import colorize_ansi

def xxx_cyan(record):
    if 'XXX' in record.message:
        return 'cyan'

class ColorFormatter(logging.Formatter):
    """
    A color Formatter for the logging standard module.

    By default, colorize CRITICAL and ERROR in red, WARNING in orange, INFO in
    green and DEBUG in yellow.

    self.colors is customizable via the 'color' constructor argument (dictionnary).

    self.colorfilters is a list of functions that get the LogRecord
    and return a color name or None.
    """

    def __init__(self, fmt=None, datefmt=None, colors=None):
        logging.Formatter.__init__(self, fmt, datefmt)
        self.colorfilters = []
        self.colors = {'CRITICAL': 'red',
                       'ERROR': 'red',
                       'WARNING': 'magenta',
                       'INFO': 'green',
                       'DEBUG': 'yellow',
                       }
        if colors is not None:
            assert isinstance(colors, dict)
            self.colors.update(colors)

    def format(self, record):
        msg = logging.Formatter.format(self, record)
        if record.levelname in self.colors:
            color = self.colors[record.levelname]
            return colorize_ansi(msg, color)
        else:
            for cf in self.colorfilters:
                color = cf(record)
                if color: 
                    return colorize_ansi(msg, color)
        return msg

def set_color_formatter(logger=None, **kw):
    """
    Install a color formatter on the 'logger'. If not given, it will
    defaults to the default logger.

    Any additional keyword will be passed as-is to the ColorFormatter
    constructor.
    """
    if logger is None:
        logger = logging.getLogger()
        if not logger.handlers:
            logging.basicConfig()
    format_msg = logger.handlers[0].formatter._fmt
    fmt = ColorFormatter(format_msg, **kw)
    fmt.colorfilters.append(xxx_cyan)
    logger.handlers[0].setFormatter(fmt)
