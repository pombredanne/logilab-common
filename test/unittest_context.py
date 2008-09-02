TEST = """
from __future__ import with_statement
from os.path import isdir, exists
import shutil
from logilab.common.testlib import TestCase, unittest_main
from logilab.common.context import tempdir

class ContextTC(TestCase):

    def test_withtempdir(self):
        with tempdir() as tmpdir:
            assert exists(tmpdir)
            assert isdir(tmpdir)
        assert not exists(tmpdir)
        try:
            with tempdir() as tmpdir:
                assert exists(tmpdir)
                shutil.rmtree(tmpdir)
        except OSError:
            pass
        else:
            self.assertTrue(False, "we should fail")
        assert not exists(tmpdir)
        with tempdir(ignore_error=True) as tmpdir:
            shutil.rmtree(tmpdir)
        def rmtree_handler(func, path, excinfo):
            self.assertTrue(issubclass(excinfo[0], OSError))
        with tempdir(onerror=rmtree_handler) as tmpdir:
            shutil.rmtree(tmpdir)
try:
    unittest_main()
except SystemExit:
    pass
"""

import sys
if sys.version_info[:2] >= (2, 5):
    exec(TEST)
