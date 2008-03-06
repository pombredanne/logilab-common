"""
Unittests for date helpers
"""

from logilab.common.testlib import TestCase, unittest_main

from logilab.common.date import date_range

try:
    from mx.DateTime import Date, RelativeDate
    from logilab.common.date import endOfMonth, add_days_worked, nb_open_days
except ImportError:
    from datetime import date as Date
    endOfMonth = add_days_worked = nb_open_days = None

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

    def test_add_days_worked(self):
        if add_days_worked is None:
            self.skip('mx.DateTime is not installed')
        add = add_days_worked
        # normal
        self.assertEquals(add(Date(2008, 1, 3), 1), Date(2008, 1, 4))
        # skip week-end
        self.assertEquals(add(Date(2008, 1, 3), 2), Date(2008, 1, 7))
        # skip 2 week-ends
        self.assertEquals(add(Date(2008, 1, 3), 8), Date(2008, 1, 15))
        # skip holiday + week-end
        self.assertEquals(add(Date(2008, 4, 30), 2), Date(2008, 5, 4))

    def test_nb_open_days(self):
        if nb_open_days is None:
            self.skip('mx.DateTime is not installed')
        nb = nb_open_days
        self.assertEquals(nb(Date(2008, 3, 4), Date(2008, 3, 7)), 3) 
        self.assertEquals(nb(Date(2008, 3, 4), Date(2008, 3, 5)), 1) 
        self.assertEquals(nb(Date(2008, 3, 7), Date(2008, 3, 10)), 1) 
        self.assertEquals(nb(Date(2008, 3, 7), Date(2008, 3, 17)), 6) 
        self.assertEquals(nb(Date(2008, 3, 18), Date(2008, 3, 26)), 5) 
        self.assertEquals(nb(Date(2008, 3, 7), Date(2008, 3, 8)), 1) 
        self.assertEquals(nb(Date(2008, 3, 7), Date(2008, 3, 9)), 1) 
        self.assertEquals(nb(Date(2008, 3, 8), Date(2008, 3, 9)), 0) 
        self.assertEquals(nb(Date(2008, 3, 8), Date(2008, 3, 10)), 0) 
        self.assertEquals(nb(Date(2008, 3, 8), Date(2008, 3, 11)), 1) 
    
if __name__ == '__main__':
    unittest_main()
