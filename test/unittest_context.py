TEST = """
from __future__ import with_statement
from os.path import isdir, exists

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
                raise Exception
        except:
            pass
        assert not exists(tmpdir)
try:
    unittest_main()
except SystemExit:
    pass
"""

import sys
if sys.version_info[:2] >= (2, 5):
    exec(TEST)
