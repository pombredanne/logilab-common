# pylint: disable-msg=E0601,W0622,W0611
#
# Copyright (c) 2004-2005 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""some wrapper around tools introduced into python 2.3, making them available
in python 2.2
"""
from __future__ import generators

__revision__ = '$Id: compat.py,v 1.13 2006-01-03 15:31:15 syt Exp $'

from logilab.common import class_renamed
from warnings import warn

try:
    set = set    
except NameError:
    try:
        from sets import Set as set
    except ImportError:
        class set:
            def __init__(self, values=()):
                self._data = {}
                warn("This implementation of Set is not complete !",
                     stacklevel=2)
                for v in values:
                    self._data[v] = 1
            
            def add(self, value):
                self._data[value] = 1

            def remove(self, element):
                del self._data[element]

            def pop(self):
                return self._data.popitem()[0]

            def __or__(self, other):
                result = set(self._data.keys())
                for val in other:
                    result.add(val)
                return result
            __add__ = __or__
            
            def __and__(self, other):
                result = set()
                for val in other:
                    if val in self._data:
                        result.add(val)
                return result
            
            def __sub__(self, other):
                result = set(self._data.keys())
                for val in other:
                    if val in self._data:
                        result.remove(val)
                return result
            
            def __cmp__(self, other):
                keys = self._data.keys()
                okeys = other._data.keys()
                keys.sort()
                okeys.sort()
                return cmp(keys, okeys)
            
            def __len__(self):
                return len(self._data)

            def __repr__(self):
                elements = self._data.keys()
                return 'lcc.set(%r)' % (elements)
            __str__ = __repr__

            def __iter__(self):
                return iter(self._data)

Set = class_renamed('Set', set, 'logilab.common.compat.Set is deprecated, '
                    'use logilab.common.compat.set instead')

try:
    from itertools import izip, chain, imap
except ImportError:
    # from itertools documentation ###
    def izip(*iterables): 
        iterables = map(iter, iterables)
        while iterables:
            result = [i.next() for i in iterables]
            yield tuple(result)

    def chain(*iterables):
        for it in iterables:
            for element in it:
                yield element
                
    def imap(function, *iterables):
        iterables = map(iter, iterables)
        while True:
            args = [i.next() for i in iterables]
            if function is None:
                yield tuple(args)
            else:
                yield function(*args)                
try:
    sum = sum
    enumerate = enumerate
except NameError:
    # define the sum and enumerate functions (builtins introduced in py 2.3)
    import operator
    def sum(seq, start=0):
        """Returns the sum of all elements in the sequence"""
        return reduce(operator.add, seq, start)

    def enumerate(iterable):
        """emulates the python2.3 enumerate() function"""
        i = 0
        for val in iterable:
            yield i, val
            i += 1
        #return zip(range(len(iterable)), iterable)
try:
    sorted = sorted
    reversed = reversed
except NameError:
    def sorted(l):
        l2 = list(l)
        l2.sort()
        return l2

    def reversed(l):
        l2 = list(l)
        l2.reverse()
        return l2
