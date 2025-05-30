import calendar
import unittest
from datetime import datetime
from dateutil.relativedelta import relativedelta
from util_functions import create_date_pairs

class TestCreateDatePairs(unittest.TestCase):

    def test_create_date_pairs_default(self):
        pairs = create_date_pairs()
        self.assertIsInstance(pairs, list)
        self.assertTrue(all(isinstance(pair, tuple) for pair in pairs))

    def test_create_date_pairs_specific_date_past_raises_exception(self):
        # test with a date in the past and expect a ValueError, otherwise fail the test
        with self.assertRaises(ValueError, msg="The start date cannot be in the past."):
            create_date_pairs(2020, 1, 1)

    # test with a date a month from now and expect a list of tuples containing 2 entries per each week of the month
    def test_create_date_pairs_specific_date_future(self):
        current_date = datetime.now() + relativedelta(months=1)
        pairs = create_date_pairs(current_date.year, current_date.month, current_date.day)
        self.assertIsInstance(pairs, list)
        self.assertTrue(all(isinstance(pair, tuple) for pair in pairs))
        # calculate number of weeks in current_date month
        weeks_with_day = [week for week
                          in calendar.monthcalendar(current_date.year, current_date.month)
                          if any(current_date.day <= day != 0 for day in week)]
        count = len(weeks_with_day)
        self.assertEqual(len(pairs), count * 2)

if __name__ == '__main__':
    unittest.main()