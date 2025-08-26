from datetime import datetime
from datetime import timedelta
import calendar
from trip_classes import Trips
from typing import List
import argparse


class CustomFormatter(argparse.HelpFormatter):
    def _format_action_invocation(self, action):
        if not action.option_strings or action.nargs == 0:
            return super()._format_action_invocation(action)
        default = self._get_default_metavar_for_optional(action)
        args_string = self._format_args(action, default)
        return ', '.join(action.option_strings) + ' ' + args_string


def print_trip_results(best_tuesdays: List[Trips], best_wednesdays: List[Trips], best_overnight: List[Trips],
                       debug_hashes=False):
    def print_trip_section(title: str, trips: List[Trips]):
        if not trips:
            return

        print(f"\n=== {title} ===")
        for i, trip in enumerate(trips, 1):
            print(f"\nOption {i}:")
            hash_outbound = hash(trip.outbound) if debug_hashes else ""
            hash_return = hash(trip.return_trip) if debug_hashes else ""

            print(
                f"Outbound: {trip.outbound.date} - {trip.outbound.departure_arrival}: £{trip.outbound.cost:.2f} ({trip.outbound.travel_time_str})  {hash_outbound}")
            print(
                f"Date Return: {trip.return_trip.date} - {trip.return_trip.departure_arrival}: £{trip.return_trip.cost:.2f} ({trip.return_trip.travel_time_str}) {hash_return}")
            print(f"Total cost: £{trip.cost():.2f}")

    print_trip_section(f"{'Best' if len(best_tuesdays) == 1 else 'Other Options'} Tuesday Same-Day Trips",
                       best_tuesdays)
    print_trip_section(f"{'Best' if len(best_wednesdays) == 1 else 'Other Options'} Wednesday Same-Day Trips",
                       best_wednesdays)
    print_trip_section(f"{'Best' if len(best_overnight) == 1 else 'Other Options'} Overnight Trips", best_overnight)


def create_date_pairs(date_from: datetime, date_to: datetime) -> list[tuple]:
    """Create pairs of dates for analysis."""
    # Get all Tuesdays and Wednesdays
    # Check date is not in the past
    now = datetime.now()
    dates = _get_tuesdays_wednesdays(date_from, date_to)
    pairs = []
    for i in range(len(dates)):
        # Same day pair
        if dates[i] < now.date():
            continue

        pairs.append((dates[i], dates[i]))
        # Check if there's a next date that forms a Tuesday-Wednesday pair
        if i + 1 < len(dates) and dates[i].weekday() == 1 and dates[i + 1].weekday() == 2 and (
                dates[i + 1] - dates[i]).days == 1:
            pairs.append((dates[i], dates[i + 1]))
    return pairs


def _get_tuesdays_wednesdays(date_from: datetime, date_to: datetime) -> List[datetime]:
    """Get all Tuesdays and Wednesdays of the year starting from the specified month or current date."""
    # List to store all Tuesdays and Wednesdays
    tuesdays_wednesdays = []

    # Start from the first day of the month (or current date if it's later)
    current_date = date_from

    # Loop until the end of the year
    while current_date <= date_to:
        # Check if the day is Tuesday (1) or Wednesday (2)
        if current_date.weekday() in [1, 2]:  # 0 is Monday, 1 is Tuesday, 2 is Wednesday
            # Only include dates that are today or in the future
            if current_date.date() >= datetime.today().date():
                tuesdays_wednesdays.append(current_date.date())

        # Move to the next day
        current_date += timedelta(days=1)

    return tuesdays_wednesdays
