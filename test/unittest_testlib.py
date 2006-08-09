"""unittest module for logilab.comon.testlib"""

__revision__ = '$Id: unittest_testlib.py,v 1.5 2006-02-09 22:37:46 nico Exp $'

import unittest
import os
from os.path import join, dirname, isdir, isfile
from cStringIO import StringIO
import tempfile
import shutil

from logilab.common.compat import sorted

try:
    __file__
except NameError:
    import sys
    __file__ = sys.argv[0]
    
from logilab.common.testlib import TestCase, unittest_main, SkipAwareTextTestRunner
from logilab.common.testlib import mock_object, NonStrictTestLoader, create_files

class MockTestCase(TestCase):
    def __init__(self):
        # Do not call unittest.TestCase's __init__
        pass

    def fail(self, msg):
        raise AssertionError(msg)

class UtilTC(TestCase):

    def test_mockobject(self):
        obj = mock_object(foo='bar', baz='bam')
        self.assertEquals(obj.foo, 'bar')
        self.assertEquals(obj.baz, 'bam')


    def test_create_files(self):
        chroot = tempfile.mkdtemp()
        path_to = lambda path: join(chroot, path)
        dircontent = lambda path: sorted(os.listdir(join(chroot, path)))
        try:
            self.failIf(isdir(path_to('a/')))
            create_files(['a/b/foo.py', 'a/b/c/', 'a/b/c/d/e.py'], chroot)
            # make sure directories exist
            self.failUnless(isdir(path_to('a')))
            self.failUnless(isdir(path_to('a/b')))
            self.failUnless(isdir(path_to('a/b/c')))
            self.failUnless(isdir(path_to('a/b/c/d')))
            # make sure files exist
            self.failUnless(isfile(path_to('a/b/foo.py')))
            self.failUnless(isfile(path_to('a/b/c/d/e.py')))
            # make sure only asked files were created
            self.assertEquals(dircontent('a'), ['b'])
            self.assertEquals(dircontent('a/b'), ['c', 'foo.py'])
            self.assertEquals(dircontent('a/b/c'), ['d'])
            self.assertEquals(dircontent('a/b/c/d'), ['e.py'])
        finally:
            shutil.rmtree(chroot)
            

class TestlibTC(TestCase):

    def setUp(self):
        self.tc = MockTestCase()

    def test_dict_equals(self):
        """tests TestCase.assertDictEquals"""
        d1 = {'a' : 1, 'b' : 2}
        d2 = {'a' : 1, 'b' : 3}
        d3 = dict(d1)
        self.assertRaises(AssertionError, self.tc.assertDictEquals, d1, d2)
        self.tc.assertDictEquals(d1, d3)
        self.tc.assertDictEquals(d3, d1)
        self.tc.assertDictEquals(d1, d1)

    def test_list_equals(self):
        """tests TestCase.assertListEquals"""
        l1 = range(10)
        l2 = range(5)
        l3 = range(10)
        self.assertRaises(AssertionError, self.tc.assertListEquals, l1, l2)
        self.tc.assertListEquals(l1, l1)
        self.tc.assertListEquals(l1, l3)
        self.tc.assertListEquals(l3, l1)

    def test_lines_equals(self):
        """tests assertLineEquals"""
        t1 = """some
        text
"""
        t2 = """some
        
        text"""
        t3 = """some
        text"""
        self.assertRaises(AssertionError, self.tc.assertLinesEquals, t1, t2)
        self.tc.assertLinesEquals(t1, t3)
        self.tc.assertLinesEquals(t3, t1)
        self.tc.assertLinesEquals(t1, t1)

    def test_xml_valid(self):
        """tests xml is valid"""
        valid = """<root>
        <hello />
        <world>Logilab</world>
        </root>"""
        invalid = """<root><h2> </root>"""
        self.tc.assertXMLStringWellFormed(valid)
        self.assertRaises(AssertionError, self.tc.assertXMLStringWellFormed, invalid)
        invalid = """<root><h2 </h2> </root>"""
        self.assertRaises(AssertionError, self.tc.assertXMLStringWellFormed, invalid)


    def test_set_equality_for_lists(self):
        l1 = [0, 1, 2]
        l2 = [1, 2, 3]
        self.assertRaises(AssertionError, self.tc.assertSetEqual, l1, l2)
        self.tc.assertSetEqual(l1, l1)
        self.tc.assertSetEqual([], [])
        l1 = [0, 1, 1]
        l2 = [0, 1]
        self.assertRaises(AssertionError, self.tc.assertSetEqual, l1, l2)
        self.tc.assertSetEqual(l1, l1)


    def test_set_equality_for_dicts(self):
        d1 = {'a' : 1, 'b' : 2}
        d2 = {'a' : 1}
        self.assertRaises(AssertionError, self.tc.assertSetEqual, d1, d2)
        self.tc.assertSetEqual(d1, d1)
        self.tc.assertSetEqual({}, {})

    def test_set_equality_for_iterables(self):
        self.assertRaises(AssertionError, self.tc.assertSetEqual, xrange(5), xrange(6))
        self.tc.assertSetEqual(xrange(5), range(5))
        self.tc.assertSetEqual([], ())

    def test_file_equality(self):
        foo = join(dirname(__file__), 'data', 'foo.txt')
        spam = join(dirname(__file__), 'data', 'spam.txt')        
        self.assertRaises(AssertionError, self.tc.assertFileEqual, foo, spam)
        self.tc.assertFileEqual(foo, foo)

    def test_stream_equality(self):
        foo = join(dirname(__file__), 'data', 'foo.txt')
        spam = join(dirname(__file__), 'data', 'spam.txt')        
        stream1 = file(foo)
        self.tc.assertStreamEqual(stream1, stream1)
        stream1 = file(foo)
        stream2 = file(spam)
        self.assertRaises(AssertionError, self.tc.assertStreamEqual, stream1, stream2)
        
    def test_text_equality(self):
        foo = join(dirname(__file__), 'data', 'foo.txt')
        spam = join(dirname(__file__), 'data', 'spam.txt')        
        text1 = file(foo).read()
        self.tc.assertTextEqual(text1, text1)
        text2 = file(spam).read()
        self.assertRaises(AssertionError, self.tc.assertTextEqual, text1, text2)




class GenerativeTestsTC(TestCase):
    
    def setUp(self):
        output = StringIO()
        self.runner = SkipAwareTextTestRunner(stream=output)

    def test_generative_ok(self):
        class FooTC(TestCase):
            def test_generative(self):
                for i in xrange(10):
                    yield self.assertEquals, i, i
        result = self.runner.run(FooTC('test_generative'))
        self.assertEquals(result.testsRun, 10)
        self.assertEquals(len(result.failures), 0)
        self.assertEquals(len(result.errors), 0)


    def test_generative_half_bad(self):
        class FooTC(TestCase):
            def test_generative(self):
                for i in xrange(10):
                    yield self.assertEquals, i%2, 0
        result = self.runner.run(FooTC('test_generative'))
        self.assertEquals(result.testsRun, 10)
        self.assertEquals(len(result.failures), 5)
        self.assertEquals(len(result.errors), 0)


    def test_generative_error(self):
        class FooTC(TestCase):
            def test_generative(self):
                for i in xrange(10):
                    if i == 5:
                        raise ValueError('STOP !')
                    yield self.assertEquals, i, i
                    
        result = self.runner.run(FooTC('test_generative'))
        self.assertEquals(result.testsRun, 5)
        self.assertEquals(len(result.failures), 0)
        self.assertEquals(len(result.errors), 1)


    def test_generative_error2(self):
        class FooTC(TestCase):
            def test_generative(self):
                for i in xrange(10):
                    if i == 5:
                        yield self.ouch
                    yield self.assertEquals, i, i
            def ouch(self): raise ValueError('stop !')
        result = self.runner.run(FooTC('test_generative'))
        self.assertEquals(result.testsRun, 6)
        self.assertEquals(len(result.failures), 0)
        self.assertEquals(len(result.errors), 1)


    def test_generative_setup(self):
        class FooTC(TestCase):
            def setUp(self):
                raise ValueError('STOP !')
            def test_generative(self):
                for i in xrange(10):
                    yield self.assertEquals, i, i
                    
        result = self.runner.run(FooTC('test_generative'))
        self.assertEquals(result.testsRun, 1)
        self.assertEquals(len(result.failures), 0)
        self.assertEquals(len(result.errors), 1)


class ExitFirstTC(TestCase):
    def setUp(self):
        output = StringIO()
        self.runner = SkipAwareTextTestRunner(stream=output, exitfirst=True)

    def test_failure_exit_first(self):
        class FooTC(TestCase):
            def test_1(self): pass
            def test_2(self): assert False
            def test_3(self): pass
        tests = [FooTC('test_1'), FooTC('test_2')]
        result = self.runner.run(unittest.TestSuite(tests))
        self.assertEquals(result.testsRun, 2)
        self.assertEquals(len(result.failures), 1)
        self.assertEquals(len(result.errors), 0)
        

    def test_error_exit_first(self):
        class FooTC(TestCase):
            def test_1(self): pass
            def test_2(self): raise ValueError()
            def test_3(self): pass
        tests = [FooTC('test_1'), FooTC('test_2'), FooTC('test_3')]
        result = self.runner.run(unittest.TestSuite(tests))
        self.assertEquals(result.testsRun, 2)
        self.assertEquals(len(result.failures), 0)
        self.assertEquals(len(result.errors), 1)
        
    def test_generative_exit_first(self):
        class FooTC(TestCase):
            def test_generative(self):
                for i in xrange(10):
                    yield self.assert_, False
        result = self.runner.run(FooTC('test_generative'))
        self.assertEquals(result.testsRun, 1)
        self.assertEquals(len(result.failures), 1)
        self.assertEquals(len(result.errors), 0)


class TestLoaderTC(TestCase):
    ## internal classes for test purposes ########
    class FooTC(TestCase):
        def test_foo1(self): pass
        def test_foo2(self): pass
        def test_bar1(self): pass

    class BarTC(TestCase):
        def test_bar2(self): pass
    ##############################################

    def setUp(self):
        self.loader = NonStrictTestLoader()
        self.module = TestLoaderTC # mock_object(FooTC=TestLoaderTC.FooTC, BarTC=TestLoaderTC.BarTC)
    
    def test_collect_everything(self):
        """make sure we don't change the default behaviour
        for loadTestsFromModule() and loadTestsFromTestCase
        """
        testsuite = self.loader.loadTestsFromModule(self.module)
        self.assertEquals(len(testsuite._tests), 2)
        suite1, suite2 = testsuite._tests
        self.assertEquals(len(suite1._tests) + len(suite2._tests), 4)

    def test_collect_with_classname(self):
        collected = self.loader.loadTestsFromName('FooTC', self.module)
        self.assertEquals(len(collected), 3)
        collected = self.loader.loadTestsFromName('BarTC', self.module)
        self.assertEquals(len(collected), 1)

    def test_collect_with_classname_and_pattern(self):
        data = [('FooTC.test_foo1', 1), ('FooTC.test_foo', 2), ('FooTC.test_fo', 2),
                ('FooTC.foo1', 1), ('FooTC.foo', 2), ('FooTC.whatever', 0)
                ]
        for pattern, expected_count in data:
            collected = self.loader.loadTestsFromName(pattern, self.module)
            yield self.assertEquals, len(collected), expected_count
        
    def test_collect_with_pattern(self):
        data = [('test_foo1', 1), ('test_foo', 2), ('test_bar', 2),
                ('foo1', 1), ('foo', 2), ('bar', 2), ('ba', 2),
                ('test', 4), ('ab', 0),
                ]
        for pattern, expected_count in data:
            collected = self.loader.loadTestsFromName(pattern, self.module)
            yield self.assertEquals, len(collected), expected_count

    
if __name__ == '__main__':
    unittest_main()

