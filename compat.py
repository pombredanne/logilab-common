# pylint: disable=E0601,W0622,W0611
# copyright 2003-2011 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This file is part of logilab-common.
#
# logilab-common is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option) any
# later version.
#
# logilab-common is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with logilab-common.  If not, see <http://www.gnu.org/licenses/>.
"""Wrappers around some builtins introduced in python 2.3, 2.4 and
2.5, making them available in for earlier versions of python.

See another compatibility snippets from other projects:

    :mod:`lib2to3.fixes`
    :mod:`coverage.backward`
    :mod:`unittest2.compatibility`
"""


__docformat__ = "restructuredtext en"

import os
import sys
import types
from warnings import warn

import __builtin__ as builtins # 2to3 will tranform '__builtin__' to 'builtins'

if sys.version_info < (3, 0):
    str_to_bytes = str
    def str_encode(string, encoding):
        if isinstance(string, unicode):
            return string.encode(encoding)
        return str(string)
else:
    def str_to_bytes(string):
        return str.encode(string)
    # we have to ignore the encoding in py3k to be able to write a string into a
    # TextIOWrapper or like object (which expect an unicode string)
    def str_encode(string, encoding):
        return str(string)

# XXX callable built-in seems back in all python versions
try:
    callable = builtins.callable
except AttributeError:
    from collections import Callable
    def callable(something):
        return isinstance(something, Callable)
    del Callable

# See also http://bugs.python.org/issue11776
if sys.version_info[0] == 3:
    def method_type(callable, instance, klass):
        # api change. klass is no more considered
        return types.MethodType(callable, instance)
else:
    # alias types otherwise
    method_type = types.MethodType

if sys.version_info < (3, 0):
    raw_input = raw_input
else:
    raw_input = input

# Pythons 2 and 3 differ on where to get StringIO
if sys.version_info < (3, 0):
    from cStringIO import StringIO
    FileIO = file
    BytesIO = StringIO
    reload = reload
else:
    from io import FileIO, BytesIO, StringIO
    from imp import reload

# Where do pickles come from?
try:
    import cPickle as pickle
except ImportError:
    import pickle

from logilab.common.deprecation import deprecated

# Other projects import these from here, keep providing them for
# backwards compat
any = deprecated('use builtin "any"')(any)
all = deprecated('use builtin "all"')(all)

# XXX shouldn't we remove this and just let 2to3 do his job ?
# range or xrange?
try:
    range = xrange
except NameError:
    range = range

# ConfigParser was renamed to the more-standard configparser
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        json = None
