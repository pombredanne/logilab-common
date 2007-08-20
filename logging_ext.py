# -*- encoding: iso-8859-1 -*-
# Copyright (c) 2006 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
""" Copyright (c) 2007 LOGILAB S.A. (Paris, FRANCE).
 http://www.logilab.fr/ -- mailto:contact@logilab.fr

This module provides extensions to the logging module from the standard library.
"""

import logging

from logilab.common.textutils import colorize_ansi

class ColorFormatter(logging.Formatter):
    """
    A color Formatter for the logging standard module.

    By default, colorize CRITICAL and ERROR in red, WARNING in orange
    and INFO in yellow.

    self.colors is customizable via the constructor.

    self.colorfilters is a list of functions that get the LogRecord
    and return a color name or None.
    """

    def __init__(self, fmt=None, datefmt=None, colors=None):
        logging.Formatter.__init__(self, fmt, datefmt)
        self.colorfilters = []
        self.colors = colors or {'CRITICAL': 'red',
                                 'ERROR': 'red',
                                 'WARNING': 'magenta',
                                 'INFO': 'yellow',
                                 }
        assert isinstance(self.colors, dict)
        
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
