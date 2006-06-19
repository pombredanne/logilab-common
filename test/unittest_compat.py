"""provides unit tests for compat module"""

__revision__ = '$Id: unittest_compat.py,v 1.3 2005-08-08 10:44:10 adim Exp $'

import unittest
import sys
import types
import __builtin__
import pprint

class CompatTCMixIn:
    MODNAMES = {}
    BUILTINS = []
    
    def setUp(self):
        self.builtins_backup = {}
        self.modules_backup = {}
        self.remove_builtins()
        self.remove_modules()
    
    def tearDown(self):
        for modname in self.MODNAMES:
            del sys.modules[modname]
        for funcname, func in self.builtins_backup.items():
            setattr(__builtin__, funcname, func)
        for modname, mod in self.modules_backup.items():
            sys.modules[modname] = mod
        try:
            del sys.modules['logilab.common.compat']
        except KeyError:
            pass
            
    def remove_builtins(self):
        for builtin in self.BUILTINS:
            func = getattr(__builtin__, builtin, None)
            if func is not None:
                self.builtins_backup[builtin] = func
                delattr(__builtin__, builtin)

    def remove_modules(self):
        for modname in self.MODNAMES:
            if modname in sys.modules:
                self.modules_backup[modname] = sys.modules[modname]
            sys.modules[modname] = types.ModuleType('faked%s' % modname)
    
    def test_removed_builtins(self):
        """tests that builtins are actually uncallable"""
        for builtin in self.BUILTINS:
            self.assertRaises(NameError, eval, builtin)

    def test_removed_modules(self):
        """tests that builtins are actually emtpy"""
        for modname, funcnames in self.MODNAMES.items():
            import_stmt = 'from %s import %s' % (modname, ', '.join(funcnames))
            # FIXME: use __import__ instead
            code = compile(import_stmt, 'foo.py', 'exec')
            self.assertRaises(ImportError, eval, code)


class Py23CompatTC(CompatTCMixIn, unittest.TestCase):
    BUILTINS = ('enumerate', 'sum')
    MODNAMES = {
        'sets' : ('Set', 'ImmutableSet'),
        'itertools' : ('izip', 'chain'),
        }

    def test_sum(self):
        from logilab.common.compat import sum
        self.assertEquals(sum(range(5)), 10)
        self.assertRaises(TypeError, sum, 'abc')
    
    def test_enumerate(self):
        from logilab.common.compat import enumerate
        self.assertEquals(list(enumerate([])), [])
        self.assertEquals(list(enumerate('abc')),
                          [(0, 'a'), (1, 'b'), (2, 'c')])

    def test_basic_set(self):
        from logilab.common.compat import set
        s = set('abc')
        self.assertEquals(len(s), 3)
        s.remove('a')
        self.assertEquals(len(s), 2)
        s.add('a')
        self.assertEquals(len(s), 3)
        s.add('a')
        self.assertEquals(len(s), 3)
        self.assertRaises(KeyError, s.remove, 'd')

    def test_basic_set(self):
        from logilab.common.compat import set
        s = set('abc')
        self.assertEquals(len(s), 3)
        s.remove('a')
        self.assertEquals(len(s), 2)
        s.add('a')
        self.assertEquals(len(s), 3)
        s.add('a')
        self.assertEquals(len(s), 3)
        self.assertRaises(KeyError, s.remove, 'd')
        self.assertRaises(TypeError, dict, [(s, 'foo')])


    def test_frozenset(self):
        from logilab.common.compat import frozenset
        s = frozenset('abc')
        self.assertEquals(len(s), 3)
        self.assertRaises(AttributeError, getattr, s, 'remove')
        self.assertRaises(AttributeError, getattr, s, 'add')
        d = {s : 'foo'} # frozenset should be hashable
        d[s] = 'bar'
        self.assertEquals(len(d), 1)
        self.assertEquals(d[s], 'bar')
        

class Py24CompatTC(CompatTCMixIn, unittest.TestCase):
    BUILTINS = ('reversed', 'sorted', 'set', 'frozenset',)
    
    def test_sorted(self):
        from logilab.common.compat import sorted
        l = [3, 1, 2, 5, 4]
        s = sorted(l)
        self.assertEquals(s, [1, 2, 3, 4, 5])
        self.assertEquals(l, [3, 1, 2, 5, 4])
        self.assertEquals(sorted('FeCBaD'), list('BCDFae'))
        self.assertEquals(sorted('FeCBaD', key=str.lower), list('aBCDeF'))
        self.assertEquals(sorted('FeCBaD', key=str.lower, reverse=True), list('FeDCBa'))
        def strcmp(s1, s2):
            return cmp(s1.lower(), s2.lower())
        self.assertEquals(sorted('FeCBaD', cmp=strcmp), list('aBCDeF'))


    def test_reversed(self):
        from logilab.common.compat import reversed
        l = range(5)
        r = reversed(l)
        self.assertEquals(r, [4, 3, 2, 1, 0])
        self.assertEquals(l, range(5))
        
    def test_set(self):
        from logilab.common.compat import set
        s1 = set(range(5))
        s2 = set(range(2, 6))
        self.assertEquals(len(s1), 5)
        self.assertEquals(s1 & s2, set([2, 3, 4]))
        self.assertEquals(s1 | s2, set(range(6)))



if __name__ == '__main__':
    unittest.main()

