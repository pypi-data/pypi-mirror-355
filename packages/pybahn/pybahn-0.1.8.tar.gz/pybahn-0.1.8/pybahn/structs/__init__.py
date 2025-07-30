from enum import StrEnum, Enum
from datetime import datetime


class Date:
    def __init__(self):
        self.date = datetime.now()

    def set_time(self, hour: int, minute: int):
        if 0 <= hour < 24 and 0 <= minute < 60:
            self.date = self.date.replace(hour=hour, minute=minute)
        else:
            raise ValueError("Invalid hour or minute")

    def set_date(self, month: int, day: int):
        if 1 <= month <= 12 and 1 <= day <= 31:
            self.date = self.date.replace(month=month, day=day)
        else:
            raise ValueError("Invalid month or day")

    def get(self) -> str:
        return self.date.replace(microsecond=0).isoformat()




class Filter(StrEnum):
    """
    Args:
        IC: - IC(intercity), EC(eurocity).
        FLX: - means trains like NJ, FLX, RJ etc.
        S: - S-Bahn(city train).
        U: - U-Bahn(underground).

    
    ``Example of use``::
    
        from pybahn import PyBahn
        from pybahn.structs import Filter

        client = PyBahn(__name__)

        station = client.station("Frankfurt")
        departures = client.departures(id=station.id, filters=[Filter.TRAM])

        print(departures[0].canceled)
    ..

    or 
    ::
        departures = client.departures(id=station.id, filters=[Filter["TRAM"]])
    ..
    """
    ICE = "&verkehrsmittel[]=ICE"
    IC = "&verkehrsmittel[]=EC_IC"
    FLX = "&verkehrsmittel[]=IR"
    RB_RE = "&verkehrsmittel[]=REGIONAL"
    S = "&verkehrsmittel[]=SBAHN"
    U = "&verkehrsmittel[]=UBAHN"
    BUS = "&verkehrsmittel[]=BUS"
    TRAM = "&verkehrsmittel[]=TRAM"
    RUF = "&verkehrsmittel[]=ANRUFPFLICHTIG"
    BOAT = "&verkehrsmittel[]=SCHIFF"

    ALL = "&verkehrsmittel[]=ICE&verkehrsmittel[]=EC_IC&verkehrsmittel[]=IR&verkehrsmittel[]=REGIONAL&verkehrsmittel[]=SBAHN&verkehrsmittel[]=UBAHN&verkehrsmittel[]=BUS&verkehrsmittel[]=TRAM&verkehrsmittel[]=ANRUFPFLICHTIG&verkehrsmittel[]=SCHIFF"
    REGIONALS = "&verkehrsmittel[]=REGIONAL&&verkehrsmittel[]=SBAHN&verkehrsmittel[]=UBAHN&verkehrsmittel[]=BUS&verkehrsmittel[]=TRAM&verkehrsmittel[]=ANRUFPFLICHTIG&verkehrsmittel[]=SCHIFF"
    HIGH_SPEED = "&verkehrsmittel[]=ICE&verkehrsmittel[]=EC_IC&verkehrsmittel[]=IR"

class Products(Enum):
    """
    ``Example of use``::
    
        from pybahn import PyBahn
        from pybahn.structs import Products

        client = PyBahn(__name__)

        station1 = client.station("Frankfurt")

        station2 = client.station("Berlin")
        
        journeys = client.journeys(station1, station2, products=[Products.REGIONAL])

        print(journeys[0])
    ..
    """
    ICE = "ICE"
    EC_IC = "EC_IC"
    IR = "IR"
    REGIONAL = "REGIONAL"
    SBAHN = "SBAHN"
    UBAHN = "UBAHN"
    BUS = "BUS"
    TRAM = "TRAM"
    RUF = "ANRUFPFLICHTIG"
    
    REGIONALS = ["REGIONAL", "SBAHN", "UBAHN", "BUS", "TRAM", "ANRUFPFLICHTIG"]
    ALL = ["ICE", "EC_IC", "IR", "REGIONAL", "SBAHN", "UBAHN", "BUS", "TRAM", 'ANRUFPFLICHTIG']

__all__ = ["Products", "Filter", "Date"]