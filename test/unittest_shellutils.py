"""unit tests for logilab.common.shellutils"""

import sys, os, tempfile, shutil
from os.path import join

from logilab.common.testlib import TestCase, unittest_main

from logilab.common.fileutils import *

DATA_DIR = 'data'

class FindTC(TestCase):
    def test_include(self):
        files = find(DATA_DIR, '.py')
        self.assertSetEqual(files,
                            [join('data', f) for f in ['__init__.py', 'module.py',
                                                       'module2.py', 'noendingnewline.py',
                                                       'nonregr.py', join('sub', 'momo.py')]])
        files = find(DATA_DIR, ('.py',), blacklist=('sub',))
        self.assertSetEqual(files,
                            [join('data', f) for f in ['__init__.py', 'module.py',
                                                       'module2.py', 'noendingnewline.py',
                                                       'nonregr.py']])
        
    def test_exclude(self):
        files = find(DATA_DIR, ('.py', '.pyc'), exclude=True)
        self.assertSetEqual(files,
                            [join('data', f) for f in ['foo.txt',
                                                       'newlines.txt',
                                                       'normal_file.txt',
                                                       'test.ini',
                                                       'test1.msg',
                                                       'test2.msg',
                                                       'spam.txt',
                                                       join('sub', 'doc.txt'),
                                                       'write_protected_file.txt',
                                                       ]])
        
#    def test_exclude_base_dir(self):
#        self.assertEquals(files_by_ext(DATA_DIR, include_exts=('.py',), exclude_dirs=(DATA_DIR,)),
#                          [])

if __name__ == '__main__':
    unittest_main()
