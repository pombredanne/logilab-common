# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
""" Copyright (c) 2002-2006 LOGILAB S.A. (Paris, FRANCE).
 http://www.logilab.fr/ -- mailto:contact@logilab.fr
 
Logilab common libraries
"""

from __future__ import nested_scopes

# bw compat
from logilab.common.graph import get_cycles

# FIXME: move all those functions in a separated module

def intersection(list1, list2):
    """return the intersection of list1 and list2"""
    intersect_dict, result = {}, []
    for item in list1:
        intersect_dict[item] = 1
    for item in list2:
        if intersect_dict.has_key(item):
            result.append(item)
    return result

def difference(list1, list2):
    """return elements of list1 not in list2"""
    tmp, result = {}, []
    for i in list2:
        tmp[i] = 1
    for i in list1:
        if not tmp.has_key(i):
            result.append(i)
    return result

def union(list1, list2):
    """return list1 union list2"""
    tmp = {}
    for i in list1:
        tmp[i] = 1
    for i in list2:
        tmp[i] = 1
    return tmp.keys()

def make_domains(lists):
    """
    given a list of lists, return a list of domain for each list to produce all
    combinaisons of possibles values

    ex: (['a', 'b'], ['c','d', 'e'])
       -> (['a', 'b', 'a', 'b', 'a', 'b'],
           ['c', 'c', 'd', 'd', 'e', 'e'])
    """
    domains = []
    for iterable in lists:
        new_domain = iterable[:]
        for i in range(len(domains)):
            domains[i] = domains[i]*len(iterable)
        if domains:
            missing = (len(domains[0]) - len(iterable)) / len(iterable)
            i = 0
            for j in range(len(iterable)):
                value = iterable[j]
                for dummy in range(missing):
                    new_domain.insert(i, value)
                    i += 1
                i += 1
        domains.append(new_domain)
    return domains


def flatten(iterable, tr_func=None, results=None):
    """flatten a list of list with any level

    if tr_func is not None, it should be a one argument function that'll be called
    on each final element
    """
    if results is None:
        results = []
    for val in iterable:
        if type(val) in (type(()), type([])):
            flatten(val, tr_func, results)
        elif tr_func is None:
            results.append(val)
        else:
            results.append(tr_func(val))
    return results


def cached(callableobj, keyarg=None):
    """simple decorator to cache result of method call"""
    #print callableobj, keyarg, callableobj.func_code.co_argcount
    if callableobj.func_code.co_argcount == 1 or keyarg == 0:
        
        def cache_wrapper1(self, *args):
            cache = '_%s_cache_' % callableobj.__name__
            #print 'cache1?', cache
            try:
                return getattr(self, cache)
            except AttributeError:
                #print 'miss'
                value = callableobj(self, *args)
                setattr(self, cache, value)
                return value
        return cache_wrapper1
    
    elif keyarg:
        
        def cache_wrapper2(self, *args, **kwargs):
            cache = '_%s_cache_' % callableobj.__name__
            key = args[keyarg-1]
            #print 'cache2?', cache, self, key
            try:
                _cache = getattr(self, cache)
            except AttributeError:
                #print 'init'
                _cache = {}
                setattr(self, cache, _cache)
            try:
                return _cache[key]
            except KeyError:
                #print 'miss', self, cache, key
                _cache[key] = callableobj(self, *args, **kwargs)
            return _cache[key]
        return cache_wrapper2
    def cache_wrapper3(self, *args):
        cache = '_%s_cache_' % callableobj.__name__
        #print 'cache3?', cache, self, args
        try:
            _cache = getattr(self, cache)
        except AttributeError:
            #print 'init'
            _cache = {}
            setattr(self, cache, _cache)
        try:
            return _cache[args]
        except KeyError:
            #print 'miss'
            _cache[args] = callableobj(self, *args)
        return _cache[args]
    return cache_wrapper3

import sys

class ProgressBar(object):
    """a simple text progression bar"""
    
    def __init__(self, nbops, size=20., stream=sys.stdout):
        self._dotevery = max(nbops / size, 1)
        self._fstr = '\r[%-20s]'
        self._dotcount, self._dots = 1, []
        self._stream = stream

    def update(self):
        """update the progression bar"""
        self._dotcount += 1
        if self._dotcount >= self._dotevery:
            self._dotcount = 1
            self._dots.append('.')
            self._stream.write(self._fstr % ''.join(self._dots))
            self._stream.flush()


import tempfile
import os
import time
from os.path import exists

class Execute:
    """This is a deadlock save version of popen2 (no stdin), that returns
    an object with errorlevel, out and err
    """
    
    def __init__(self, command):
        outfile = tempfile.mktemp()
        errfile = tempfile.mktemp()
        self.status = os.system("( %s ) >%s 2>%s" %
                                (command, outfile, errfile)) >> 8
        self.out = open(outfile,"r").read()
        self.err = open(errfile,"r").read()
        os.remove(outfile)
        os.remove(errfile)

def acquire_lock(lock_file, max_try=10, delay=10):
    """acquire a lock represented by a file on the file system"""
    count = 0
    while max_try <= 0 or count < max_try:
        if not exists(lock_file):
            break
        count += 1
        time.sleep(delay)
    else:
        raise Exception('Unable to acquire %s' % lock_file)
    stream = open(lock_file, 'w')
    stream.write(str(os.getpid()))
    stream.close()
    
def release_lock(lock_file):
    """release a lock represented by a file on the file system"""
    os.remove(lock_file)


## Deprecation utilities #########################

from warnings import warn

class deprecated(type):
    """metaclass to print a warning on instantiation of a deprecated class"""
    
    def __call__(cls, *args, **kwargs):
        msg = getattr(cls, "__deprecation_warning__",
                      "%s is deprecated" % cls.__name__)
        warn(msg, DeprecationWarning, stacklevel=2)
        return type.__call__(cls, *args, **kwargs)


def class_renamed(old_name, new_class, message=None):
    """automatically creates a class which fires a DeprecationWarning
    when instantiated.
    
    >>> Set = class_renamed('Set', set, 'Set is now replaced by set')
    >>> s = Set()
    sample.py:57: DeprecationWarning: Set is now replaced by set
      s = Set()
    >>>
    """
    clsdict = {}
    if message is not None:
        clsdict['__deprecation_warning__'] = message
    try:
        # new-style class
        return deprecated(old_name, (new_class,), clsdict)
    except (NameError, TypeError):
        # old-style class
        class DeprecatedClass(new_class):
            """FIXME: There might be a better way to handle old/new-style class
            """
            def __init__(self, *args, **kwargs):
                warn(message, DeprecationWarning, stacklevel=2)
                new_class.__init__(self, *args, **kwargs)
        return DeprecatedClass


def deprecated_function(new_func, message=None):
    """creates a function which fires a DeprecationWarning when used

    For example, if <bar> is deprecated in favour of <foo> :
    >>> bar = deprecated_function(foo, 'bar is deprecated')
    >>> bar()
    sample.py:57: DeprecationWarning: bar is deprecated
      bar()
    >>>
    """
    if message is None:
        message = "this function is deprecated, use %s instead" % (
            new_func.func_name)
    def deprecated(*args, **kwargs):
        warn(message, DeprecationWarning, stacklevel=2)
        return new_func(*args, **kwargs)
    return deprecated
