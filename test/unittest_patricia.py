"""
unit tests for module logilab.common.patricia
"""

__revision__ = "$Id: unittest_patricia.py,v 1.3 2003-09-05 10:22:35 syt Exp $"

from logilab.common.patricia import *
from logilab.common.testlib import TestCase, unittest_main
    
class PatriciaTrieClassTest(TestCase):
    
    def test_knownValues(self):
        """ 
        remove a child node
        """
        p = PatriciaTrie()
        i = 0
        words_list = ['maitre', 'maman', 'mange', 'manger', 'mangouste',
                      'manigance', 'manitou']
        words_list.sort()
        #
        for i in range(len(words_list)):
            p.insert(words_list[i], i)
        for i in range(len(words_list)):
            assert p.lookup(words_list[i]) == [i]
        try:
            p.lookup('not in list')
            raise AssertionError()
        except KeyError:
            pass
        #
        l = p.pfx_search('')
        l.sort()
        assert l == words_list
        l = p.pfx_search('ma')
        l.sort()
        assert l == words_list
        l = p.pfx_search('mai')
        assert l == ['maitre']
        l = p.pfx_search('not in list')
        assert l == []
        l = p.pfx_search('man', 2)
        assert l == ['mange']
        l = p.pfx_search('man', 1)
        assert l == []
        p.remove('maitre')
        try:
            p.lookup('maitre')
            raise AssertionError()
        except KeyError:
            pass
        #print p
    

if __name__ == '__main__':
    unittest_main()
