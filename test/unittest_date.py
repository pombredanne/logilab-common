"""
Unittests for date helpers
"""

from logilab.common.testlib import TestCase, unittest_main

from logilab.common.date import date_range

try:
    from mx.DateTime import Date, RelativeDate
    from logilab.common.date import endOfMonth
except ImportError:
    from datetime import date as Date
    endOfMonth = None

class DateTC(TestCase):
    
    def test_day(self):
        """enumerate days"""
        r = list(date_range(Date(2000,1,1), Date(2000,1,4)))
        expected = [Date(2000,1,1), Date(2000,1,2), Date(2000,1,3)]
        self.assertListEquals(r, expected)
        r = list(date_range(Date(2000,1,31), Date(2000,2,3)))
        expected = [Date(2000,1,31), Date(2000,2,1), Date(2000,2,2)]
        self.assertListEquals(r, expected)

    def test_month(self):
        """enumerate months"""
        if endOfMonth is None:
            self.skip('mx.DateTime is not installed')
        r = list(date_range(Date(2000,1,2), Date(2000,4,4), endOfMonth))
        expected = [Date(2000,1,2), Date(2000,2,29), Date(2000,3,31)]
        self.assertListEquals(r, expected)
        r = list(date_range(Date(2000,11,30), Date(2001,2,3), endOfMonth))
        expected = [Date(2000,11,30), Date(2000,12,31), Date(2001,1,31)]
        self.assertListEquals(r, expected)

    
if __name__ == '__main__':
    unittest_main()
