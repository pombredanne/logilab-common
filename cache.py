"""Cache module, with a least recently used algorithm for the management of the
deletion of entries.

:copyright: 2002-2008 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
:contact: http://www.logilab.fr/ -- mailto:contact@logilab.fr
:license: General Public License version 2 - http://www.gnu.org/licenses
"""
__docformat__ = "restructuredtext en"

from threading import Lock

from logilab.common.decorators import locked

_marker = object()

class Cache:
    """A dictionnary like cache.

    inv:
        len(self._usage) <= self.size
        len(self.data) <= self.size
    """
    
    def __init__(self, size=100):
        assert size >= 0, 'cache size must be >= 0 (0 meaning no caching)'
        self.data = {}
        self.size = size
        self._usage = []
        self._lock = Lock()
        
    def __repr__(self):
        return repr(self.data)

    def __len__(self):
        return len(self.data)

    def _acquire(self):
        self._lock.acquire()

    def _release(self):
        self._lock.release()

    def _update_usage(self, key):
        if not self._usage:
            self._usage.append(key)        
        elif self._usage[-1] != key:
            try:
                self._usage.remove(key)
            except ValueError:
                # we are inserting a new key
                # check the size of the dictionnary
                # and remove the oldest item in the cache
                if self.size and len(self._usage) >= self.size:
                    del self.data[self._usage[0]]
                    del self._usage[0]
            self._usage.append(key)
        else:
            pass # key is already the most recently used key
            
    def __getitem__(self, key):
        value = self.data[key]
        self._update_usage(key)
        return value
    __getitem__ = locked(_acquire, _release)(__getitem__)
    
    def __setitem__(self, key, item):
        # Just make sure that size > 0 before inserting a new item in the cache
        if self.size > 0:
            self.data[key] = item
            self._update_usage(key)
    __setitem__ = locked(_acquire, _release)(__setitem__)
        
    def __delitem__(self, key):
        del self.data[key]
        self._usage.remove(key)
    __delitem__ = locked(_acquire, _release)(__delitem__)
    
    def pop(self, value, default=_marker):
        if value in self.data:
            self._usage.remove(value)
        if default is _marker:
            return self.data.pop(value)
        return self.data.pop(value, default)
    pop = locked(_acquire, _release)(pop)
    
    def clear(self):
        self.data.clear()
        self._usage = []
    clear = locked(_acquire, _release)(clear)

    def keys(self):
        return self.data.keys()

    def items(self):
        return self.data.items()

    def values(self):
        return self.data.values()

    def has_key(self, key):
        return self.data.has_key(key)
    
    __contains__ = has_key
    
