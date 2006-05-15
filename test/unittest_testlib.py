"""unittest module for logilab.comon.testlib"""

__revision__ = '$Id: unittest_testlib.py,v 1.5 2006-02-09 22:37:46 nico Exp $'

import unittest
from os.path import join, dirname
try:
    __file__
except NameError:
    import sys
    __file__ = sys.argv[0]
    
from logilab.common import testlib

class MockTestCase(testlib.TestCase):
    def __init__(self):
        # Do not call unittest.TestCase's __init__
        pass

    def fail(self, msg):
        raise AssertionError(msg)

class UtilTC(testlib.TestCase):

    def test_mockobject(self):
        obj = testlib.mock_object(foo='bar', baz='bam')
        self.assertEquals(obj.foo, 'bar')
        self.assertEquals(obj.baz, 'bam')

class TestlibTC(testlib.TestCase):

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
    
if __name__ == '__main__':
    testlib.unittest_main()

