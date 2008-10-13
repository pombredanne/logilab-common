import sys
from logilab.common.testlib import TestCase, unittest_main, TestSuite
from logilab.common.decorators import require_version, require_module

class DecoratorsTC(TestCase):
    def test_require_version_good(self):
        """ should return the same function
        """
        def func() :
            pass
        sys.version_info = (2, 5, 5, 'final', 4)
        current = sys.version_info[:3]
        compare = ('2.4', '2.5', '2.5.4', '2.5.5')
        for version in compare: 
            decorator = require_version(version)
            self.assertEquals(func, decorator(func), '%s =< %s : function \
                return by the decorator should be the same.' % (version, 
                '.'.join([str(element) for element in current])))

    def test_require_version_bad(self):
        """ should return a different function : skipping test
        """
        def func() :
            pass
        sys.version_info = (2, 5, 5, 'final', 4)
        current = sys.version_info[:3]
        compare = ('2.5.6', '2.6', '2.6.5')
        for version in compare: 
            decorator = require_version(version)
            self.assertNotEquals(func, decorator(func), '%s >= %s : function \
                 return by the decorator should NOT be the same.' 
                 % ('.'.join([str(element) for element in current]), version))

    def test_require_version_exception(self):
        """ should throw a ValueError exception
        """
        def func() :
            pass
        compare = ('2.5.a', '2.a', 'azerty')
        for version in compare: 
            decorator = require_version(version)
            self.assertRaises(ValueError, decorator, func)

    def test_require_module_good(self):
        """ should return the same function
        """
        def func() :
            pass
        module = 'sys'
        decorator = require_module(module)
        self.assertEquals(func, decorator(func), 'module %s exists : function \
            return by the decorator should be the same.' % module)

    def test_require_module_bad(self):
        """ should return a different function : skipping test
        """
        def func() :
            pass
        modules = ('bla', 'blo', 'bli')
        for module in modules:
            try:
                __import__(module)
                pass
            except ImportError:
                decorator = require_module(module)
                self.assertNotEquals(func, decorator(func), 'module %s does \
                    not exist : function return by the decorator should \
                    NOT be the same.' % module)
                return
        print 'all modules in %s exist. Could not test %s' % (', '.join(modules), 
            sys._getframe().f_code.co_name)

if __name__ == '__main__':
    unittest_main()
