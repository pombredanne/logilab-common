"""
Unittests for date helpers
"""

from logilab.common.testlib import TestCase, unittest_main

from logilab.common.date import date_range

try:
    from mx.DateTime import Date, RelativeDate, RelativeDateTime, now, DateTime
    from logilab.common.date import endOfMonth, add_days_worked, nb_open_days, \
         get_national_holidays
except ImportError:
    from datetime import date as Date, datetime as DateTime, timedelta as RelativeDateTime
    now = DateTime.now
    get_national_holidays = endOfMonth = add_days_worked = nb_open_days = None

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
        self.check_mx()
        r = list(date_range(Date(2000,1,2), Date(2000,4,4), endOfMonth))
        expected = [Date(2000,1,2), Date(2000,2,29), Date(2000,3,31)]
        self.assertListEquals(r, expected)
        r = list(date_range(Date(2000,11,30), Date(2001,2,3), endOfMonth))
        expected = [Date(2000,11,30), Date(2000,12,31), Date(2001,1,31)]
        self.assertListEquals(r, expected)

    def test_add_days_worked(self):
        self.check_mx()
        add = add_days_worked
        # normal
        self.assertEquals(add(Date(2008, 1, 3), 1), Date(2008, 1, 4))
        # skip week-end
        self.assertEquals(add(Date(2008, 1, 3), 2), Date(2008, 1, 7))
        # skip 2 week-ends
        self.assertEquals(add(Date(2008, 1, 3), 8), Date(2008, 1, 15))
        # skip holiday + week-end
        self.assertEquals(add(Date(2008, 4, 30), 2), Date(2008, 5, 5))

    def test_get_national_holidays(self):
        self.check_mx()
        holidays = get_national_holidays
        yield self.assertEquals, holidays(Date(2008, 4, 29), Date(2008, 5, 2)), \
              [Date(2008, 5, 1)]
        yield self.assertEquals, holidays(Date(2008, 5, 7), Date(2008, 5, 8)), []
        x = DateTime(2008, 5, 7, 12, 12, 12)
        yield self.assertEquals, holidays(x, x+1), []

    def test_open_days_now_and_before(self):
        self.check_mx()
        nb = nb_open_days
        x = now()
        y = x - RelativeDateTime(seconds=1)
        self.assertRaises(AssertionError, nb, x, y)

    def check_mx(self):
        if nb_open_days is None:
            self.skip('mx.DateTime is not installed')        

    def assertOpenDays(self, start, stop, expected):
        self.check_mx()
        got = nb_open_days(start, stop)
        self.assertEquals(got, expected)

    def test_open_days_tuesday_friday(self):
        self.assertOpenDays(Date(2008, 3, 4), Date(2008, 3, 7), 3)

    def test_open_days_day_nextday(self):
        self.assertOpenDays(Date(2008, 3, 4), Date(2008, 3, 5), 1)

    def test_open_days_friday_monday(self):
        self.assertOpenDays(Date(2008, 3, 7), Date(2008, 3, 10), 1)

    def test_open_days_friday_monday_with_two_weekends(self):
        self.assertOpenDays(Date(2008, 3, 7), Date(2008, 3, 17), 6)

    def test_open_days_tuesday_wednesday(self):
        """week-end + easter monday"""
        self.assertOpenDays(Date(2008, 3, 18), Date(2008, 3, 26), 5)

    def test_open_days_friday_saturday(self):
        self.assertOpenDays(Date(2008, 3, 7), Date(2008, 3, 8), 1)
        
    def test_open_days_friday_sunday(self):
        self.assertOpenDays(Date(2008, 3, 7), Date(2008, 3, 9), 1)

    def test_open_days_saturday_sunday(self):
        self.assertOpenDays(Date(2008, 3, 8), Date(2008, 3, 9), 0)

    def test_open_days_saturday_monday(self):
        self.assertOpenDays(Date(2008, 3, 8), Date(2008, 3, 10), 0)

    def test_open_days_saturday_tuesday(self):
        self.assertOpenDays(Date(2008, 3, 8), Date(2008, 3, 11), 1)

    def test_open_days_now_now(self):
        x = now()
        self.assertOpenDays(x, x, 0)
        
    def test_open_days_afternoon_before_holiday(self):
        self.assertOpenDays(DateTime(2008, 5, 7, 14), Date(2008, 5, 8), 1)
        
    def test_open_days_afternoon_before_saturday(self):
        self.assertOpenDays(DateTime(2008, 5, 9, 14), Date(2008, 5, 10), 1)
        
    def test_open_days_afternoon(self):
        self.assertOpenDays(DateTime(2008, 5, 6, 14), Date(2008, 5, 7), 1)
        
    def test_open_days_now_and_one_second(self):
        x = now()
        y = x + RelativeDateTime(seconds=1)
        self.assertOpenDays(x, y, 1)
        
    
if __name__ == '__main__':
    unittest_main()
