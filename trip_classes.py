import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

class TripType(Enum):
    OUTBOUND = 1
    RETURN = 2

@dataclass
class Trip:
    type: TripType
    cost: float = float("inf")
    departure_arrival: str = ""
    travel_time_str: str = ""
    travel_time_minutes: int = 0
    date: str = ""
    num_stops: int = 0

    def to_string(self, debug_trip=False) -> str:
        trip_type = 'Outbound' if self.type == TripType.OUTBOUND else 'Return'
        debug_hash = f" {hash(self)}" if debug_trip else ""
        return f"{trip_type} £{self.cost:.2f} {self.date} - {self.departure_arrival}: {self.travel_time_str} - {self.num_stops} stops {debug_hash}"

    def __eq__(self, other):
        if isinstance(other, Trip):
            return (self.type == other.type and self.cost == other.cost and
                    self.travel_time_str == other.travel_time_str and
                    self.departure_arrival == other.departure_arrival and
                    self.travel_time_minutes == other.travel_time_minutes and
                    self.date == other.date and self.num_stops == other.num_stops)
        return False

    def __hash__(self):
        return hash((self.type, self.cost, self.travel_time_str, self.departure_arrival,
                     self.travel_time_minutes, self.date, self.num_stops))

@dataclass
class Trips:
    outbound: Trip
    return_trip: Trip
    def cost(self):
        return self.outbound.cost + self.return_trip.cost

@dataclass
class Results:
    same_day_tuesday: List[Trips]
    same_day_wednesday: List[Trips]
    overnight_stays: List[Trips]

from json import JSONEncoder
from datetime import date

class TripJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, TripType):
            return {"__triptype__": obj.name}
        elif isinstance(obj, Trip):
            return {
                "__trip__": {
                    "type": obj.type,
                    "cost": obj.cost,
                    "departure_arrival": obj.departure_arrival,
                    "travel_time_str": obj.travel_time_str,
                    "travel_time_minutes": obj.travel_time_minutes,
                    "date": obj.date,
                    "num_stops": obj.num_stops
                }
            }
        elif isinstance(obj, date):
            return {"__date__": obj.isoformat()}
        return super().default(obj)

def trip_json_decoder(dct):
    if "__triptype__" in dct:
        return TripType[dct["__triptype__"]]
    elif "__trip__" in dct:
        data = dct["__trip__"]
        #data["date"] = data["date"]
        return Trip(**data)
    elif "__date__" in dct:
        return datetime.date.fromisoformat(dct["__date__"])
    return dct
