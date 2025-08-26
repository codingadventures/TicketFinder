import json
import sys

import requests
from bs4 import BeautifulSoup
import re
import argparse
import os
import tempfile
import shutil
import urllib.parse
from datetime import datetime
import util_functions
from trip_classes import Trip, Trips, Results, TripType, TripJSONEncoder, trip_json_decoder


class TooFarInAdvanceException(Exception):
    """Exception raised when the date is too far in advance."""
    pass


class TrainTicketFinder:
    def __init__(self, in_date, no_changes=True, station_from='warrington+bank+quay', station_to='london+euston',
                 disable_cache=False, max_stops=4, debug_trips=False):
        self.no_changes = no_changes
        self.disable_cache = disable_cache
        self.base_url = "https://traintimes.org.uk"
        self.url_outbound = f'https://traintimes.org.uk/{station_from}/{station_to}/10:30a'
        self.url_return = f'https://traintimes.org.uk/{station_to}/{station_from}/22:00a'
        self.scheme = "https"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://traintimes.org.uk/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

        self.cache_file = 'train_prices_cache.json'
        self.cache = self.load_cache()
        self.max_stops = max_stops
        try:
            self.session = requests.Session()
            # First visit the main page to get cookies
            # this is needed to avoid the 418 I'm a teapot error
            self.session.get(self.base_url)
        except:
            print("Failed to connect to traintimes.org")
            raise

        # Create date pairs for analysis
        date_to = datetime(in_date.year, in_date.month, 31 if in_date.day == 1 else in_date.day)
        self.date_pairs = util_functions.create_date_pairs(in_date, date_to)
        self.debug_trips = debug_trips

    def load_cache(self):
        """Load cache from a JSON file."""
        if self.disable_cache:
            return {}

        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as file:
                return json.load(file, object_hook=trip_json_decoder)
        return {}

    def save_cache(self):
        """Save cache to a JSON file."""
        # Read existing data

        try:
            with open(self.cache_file, 'r') as file:
                existing_cache = json.load(file, object_hook=trip_json_decoder)
                existing_cache.update(self.cache)
        except FileNotFoundError:
            existing_cache = self.cache

        # Write to temporary file first
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        try:
            with open(temp_file.name, 'w') as file:
                json.dump(existing_cache, file, cls=TripJSONEncoder)
            # Replace original with new file
            shutil.move(temp_file.name, self.cache_file)
        except:
            os.unlink(temp_file.name)
            raise

    @staticmethod
    def save_html_to_file(html_content, file_name="soup_output.html"):
        """Save HTML content to a file for inspection."""
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(html_content)

    def get_number_of_stops(self, url):
        try:
            cache_key = f"stops_{url}"

            # Check if the data is in the cache
            if cache_key in self.cache:
                return self.cache[cache_key]

            # Then make your actual request
            response = self.session.get(url, headers=self.headers)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Look for table rows in the calling points table, excluding header row
                stop_rows = soup.find('tbody')
                # Count rows, ignoring header row(s)
                num_stops = stop_rows.find_all('tr')
                # Save the fetched data to the cache

                self.cache[cache_key] = len(num_stops)
                self.save_cache()

                return len(num_stops)
            else:
                raise Exception(f"Error fetching stops: {response.status_code}")
        except Exception as e:
            print(f"Error fetching stops: {e}")
            return 0

    def _get_soup_from_url(self, url):
        # Make POST request
        response = self.session.post(url, headers=self.headers)

        if response.status_code != 200 and response.status_code != 422:
            print(f"Failed to fetch data for {url}: Status code {response.status_code}")
            return []

        if self.debug_trips:
            # Save the raw HTML content to a file
            self.save_html_to_file(response.text, "soup_output.html")


        # Parse HTML
        soup = BeautifulSoup(response.text, 'lxml')
        return soup

    def _get_trips_from_soup(self, soup, trip_type, date_str) -> [Trip]:
        trips: [Trip] = []

        if soup.find('div', id='warning'):
            return trips

        result_elements = soup.find_all('li', id=re.compile(r'^result\d+$'))

        for result in result_elements:

            if self.debug_trips:
                # Print the HTML of each found element
                print(f"Result {result.get('id')}:\n{result.prettify()}\n")

            if result.find('a', class_='change_link') and self.no_changes:
                continue

            trip = Trip(
                type=trip_type,
                cost=0.0,  # will be updated later
                travel_time_str="",  # will be updated later
                departure_arrival="",
                travel_time_minutes=0,  # will be updated later
                date=date_str.strftime("%B %d, %Y"),  # format: May 25, 2025
                num_stops=0
            )

            # Find the calling points link
            calling_link = result.find('a', class_="calling_link")
            num_stops = 0
            if calling_link:
                # Get the href attribute and construct the full URL
                href = calling_link.get('href')
                stops_url = urllib.parse.urljoin(self.base_url, href)

                # Get the number of stops
                num_stops = self.get_number_of_stops(stops_url)

                # Skip this train if it has too many stops
                if num_stops > self.max_stops:
                    continue

            trip.num_stops = num_stops

            # Extract the time
            time_element = result.find('strong')
            trip.departure_arrival = time_element.get_text().strip() if time_element else "Unknown"

            small_element = result.find('small')
            text = small_element.get_text()
            # Use regex to find the journey time pattern (e.g., "2h 3m")
            journey_time_match = re.search(r'(\d+h\s+\d+m)', result.small.get_text())
            if journey_time_match:
                journey_time = journey_time_match.group(1)
                hours, minutes = 0, 0
                if 'h' in journey_time:
                    hours = int(re.search(r'(\d+)h', journey_time).group(1))
                if 'm' in journey_time:
                    minutes = int(re.search(r'(\d+)m', journey_time).group(1))

                trip.travel_time_minutes = hours * 60 + minutes
                trip.travel_time_str = journey_time
            else:
                print("Journey time not found")

            # Look for Advance Single price pattern
            match = re.search(r'£(\d+\.\d+) Advance Single', text)
            if match:
                trip.cost = float(match.group(1))
            else:
                match = re.search(r'£(\d+\.\d+) Single', text)
                if match:
                    trip.cost = float(match.group(1))
                else:
                    raise TooFarInAdvanceException(f"Date {date_str} is too far in advance, there's no price yet.")

            print(trip.to_string(self.debug_trips))
            trips.append(trip)

        return trips

    def _fetch_train_prices(self, trip_date, url, trip_type) -> [Trip]:
        """Fetch train prices for the given date."""
        date_str = trip_date.strftime("%Y-%m-%d")
        cache_key = f"{date_str}_{url}"

        # Check if the data is in the cache
        if cache_key in self.cache:
            trips = self.cache[cache_key]
            for trip in trips: print(trip.to_string(self.debug_trips))
            return trips

        trips: [Trip] = []

        url_request = url + f'/{date_str}'
        soup = self._get_soup_from_url(url_request)

        # let's check this date is too far in advance
        if soup.find('p', class_='error-message'):
            raise TooFarInAdvanceException(f"Date {date_str} is too far in advance.")

        # Find all small elements that might contain fare information
        # Find the result element
        trips += self._get_trips_from_soup(soup, trip_type, trip_date)

        if trip_type == TripType.OUTBOUND:
            earlier_later_link = soup.find('a', {'data-type': 'out-earlier'})['href']
        else:
            earlier_later_link = soup.find('a', {'data-type': 'out-later'})['href']

        if earlier_later_link:
            soup = self._get_soup_from_url(self.base_url + earlier_later_link)
            trips += self._get_trips_from_soup(soup, trip_type, trip_date)

        # Save the fetched data to the cache
        self.cache[cache_key] = trips
        self.save_cache()

        return trips

    def fetch_trip_data(self) -> Results:

        trip_results: Results = Results(
            same_day_tuesday=[],
            same_day_wednesday=[],
            overnight_stays=[]
        )

        for date1, date2 in self.date_pairs:
            # Get the month key for this pair
            # Same day returns (both Tuesday and Wednesday)
            is_tuesday = date1.weekday() == date2.weekday() == 1
            is_overnight = date1.weekday() == 1 and date2.weekday() == 2
            try:
                if is_overnight:
                    continue
                else:
                    outbound_trip = self._fetch_train_prices(date1, self.url_outbound, TripType.OUTBOUND)
                    return_trip = self._fetch_train_prices(date2, self.url_return, TripType.RETURN)
            except TooFarInAdvanceException as too_far_exc:
                print(too_far_exc)
                break

            if not outbound_trip or not return_trip:
                continue

            # take only the first two from min_outbound and min_return
            min_outbound = sorted(outbound_trip, key=lambda x: (x.cost, x.travel_time_minutes))[:2]
            min_return = sorted(return_trip, key=lambda x: (x.cost, x.travel_time_minutes))[:2]

            # Create Trips objects for the selected trips
            trips = [Trips(outbound=out, return_trip=ret) for out in min_outbound for ret in min_return]
            trips = sorted(trips, key=lambda x: (x.cost()))[:2]

            if is_tuesday:
                trip_results.same_day_tuesday.extend(trips)
            else:
                trip_results.same_day_wednesday.extend(trips)

        # extract overnight stays from Tuesday and Wednesday already calculated
        for date1, date2 in self.date_pairs:
            is_overnight = date1.weekday() == 1 and date2.weekday() == 2
            if not is_overnight:
                continue

            date1 = date1.strftime("%B %d, %Y")
            date2 = date2.strftime("%B %d, %Y")

            outbound = {trips.outbound for trips in trip_results.same_day_tuesday if trips.outbound.date == date1}
            return_trip = {trips.return_trip for trips in trip_results.same_day_wednesday if
                           trips.return_trip.date == date2}
            trips = [Trips(outbound=out, return_trip=ret) for out in outbound for ret in return_trip]
            trips = sorted(trips, key=lambda x: (x.cost()))[:2]
            trip_results.overnight_stays.extend(trips)
        return trip_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Find cheapest train tickets between stations on Tuesdays and Wednesdays of a given month. This also includes best overnight stays (Tue-Wed)\n\n',
        usage='\nRequired arguments:\n'
              '\t--month MONTH     Starting month (1-12)\n'
              '\t--year YEAR       Starting year (2025)\n'
              '\nOptional arguments:\n'
              '\t--day DAY         Day of the month (1-31, default: 1)\n'
              '\t--station_from    Starting station, use + for spaces (default: warrington+bank+quay)\n'
              '\t--station_to      Final station, use + for spaces (default: london+euston)\n'
              '\t--max_stops       Maximum stops for a train journey (default: 8)\n'
              '\t--nocache         Disable caching of results\n'
              '\t--debug_trips     Enable verbose debug output',
        formatter_class=util_functions.CustomFormatter,
        epilog='Example: %(prog)s --month 6 --year 2025 --station_from "manchester+piccadilly"',
        add_help=True
    )

    group = parser.add_argument_group('date arguments')
    group.add_argument('--month', type=int, help='Starting month (1-12)', metavar='MONTH')
    group.add_argument('--year', type=int, help='Starting year', metavar='YEAR')
    group.add_argument('--day', type=int, help='Day of the month (1-31)', default=1, metavar='DAY')

    group = parser.add_argument_group('search options')
    group.add_argument('--station_from', type=str, help='Starting station (use + for spaces)',
                       default='warrington+bank+quay', metavar='STATION')
    group.add_argument('--station_to',  type=str, help='Ending station (use + for spaces)',
                       default='london+euston', metavar='STATION')

    group.add_argument('--max_stops', type=int, help='Maximum stops for a train journey', default=8, metavar='STOPS')
    group.add_argument('--no_changes', action='store_true', help='Only show direct trains', default=True)

    group = parser.add_argument_group('debug options')
    group.add_argument('--nocache', action='store_true', help='Disable caching of results')
    group.add_argument('--debug_trips', action='store_true', help='Enable verbose debug output')
    args = parser.parse_args()
    if args.month is None or args.year is None:
        parser.print_help()
        sys.exit(1)

    scraper = TrainTicketFinder( datetime(args.year, args.month, args.day) ,args.no_changes, args.station_from, args.station_to, args.nocache, args.max_stops, args.debug_trips)

    results = scraper.fetch_trip_data()

    # min_fares = scraper.calculate_min_fares(results)
    best_tuesdays = sorted(results.same_day_tuesday, key=lambda trip: trip.cost())
    best_wednesdays = sorted(results.same_day_wednesday, key=lambda trip: trip.cost())

    # let's keep only the best wednesday that cose less than the best tuesday
    if best_tuesdays and best_wednesdays:
        best_wednesdays = [trip for trip in best_wednesdays if trip.cost() < best_tuesdays[0].cost()]

    best_overnight = sorted(results.overnight_stays, key=lambda trip: trip.cost())
    util_functions.print_trip_results(best_tuesdays[:1], best_wednesdays[:1], best_overnight[:1], args.debug_trips)
    util_functions.print_trip_results(best_tuesdays[1:], best_wednesdays[1:], best_overnight[1:], args.debug_trips)