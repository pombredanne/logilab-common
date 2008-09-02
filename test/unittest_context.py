from __future__ import with_statement

import unittest
from os.path import isdir, exists

from logilab.common.testlib import TestCase
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

if __name__ == '__main__':
    unittest_main()
