"""run all astng related tests"""

__revision__ = '$Id: _test_astng.py,v 1.1 2005-04-25 14:47:04 syt Exp $'

import unittest

from unittest_astng import *
from unittest_astng_builder import *
from unittest_astng_utils import *
from unittest_astng_manager import *
from unittest_astng_inspector import *

if __name__ == '__main__':
    unittest.main()
