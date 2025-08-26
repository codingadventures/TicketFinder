# TicketFinder

**Find Cheapest Tickets**

TicketFinder is a Python-based utility designed to help users find the cheapest train tickets by searching and comparing available options. The project focuses on automating the process of ticket discovery, making it easier to plan trips and minimize travel costs.

## Features

- **Automated Ticket Search:** Quickly finds available train tickets based on your trip parameters.
- **Date Filtering:** Focuses on Tuesdays and Wednesdays of a given month, with options for overnight stays.
- **Customizable Search:** Specify stations, date range, max stops, and more.
- **Caching System:** By default, uses caching for faster repeated searches (can be disabled).
- **Debugging Tools:** Options to enable verbose output for troubleshooting and development.
- **Unit Tests:** Comprehensive test suite to ensure core logic correctness.

## Usage

TicketFinder is run from the command line with several parameters to customize your search.

### Command-Line Arguments

**Required arguments:**
- `--month MONTH`  
  Starting month (1-12)
- `--year YEAR`  
  Starting year (e.g., 2025)

**Optional arguments:**
- `--day DAY`  
  Day of the month (1-31, default: 1)
- `--station_from STATION`  
  Starting station, use `+` for spaces (default: `warrington+bank+quay`)
- `--station_to STATION`  
  Final station, use `+` for spaces (default: `london+euston`)
- `--max_stops STOPS`  
  Maximum stops for a train journey (default: 8)
- `--no_changes`  
  Only show direct trains (default: True)
- `--nocache`  
  Disable caching of results
- `--debug_trips`  
  Enable verbose debug output

### Example Usage

```bash
python train_ticket_finder.py --month 6 --year 2025 --station_from "manchester+piccadilly"
```

This will search for the cheapest train tickets from Manchester Piccadilly to London Euston in June 2025, considering only Tuesdays and Wednesdays, and using default options for other parameters.

### Full Usage Help

You can print out the help with:

```bash
python train_ticket_finder.py --help
```

This will show all options with descriptions.

## Project Structure

```
.
├── .gitattributes
├── .idea/                # Project configuration files (IDE-specific)
├── LICENSE
├── UnitTests/            # Unit tests for the main logic
├── train_ticket_finder.py    # Main ticket finder logic
├── trip_classes.py           # Trip classes and related logic
└── util_functions.py         # Utility functions
```

## Testing

To run the unit tests:

```bash
python -m unittest discover UnitTests
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please fork the repo and submit pull requests.

---

*Repository: [codingadventures/TicketFinder](https://github.com/codingadventures/TicketFinder)*