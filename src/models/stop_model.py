from src.core.model import DBModel
from functools import lru_cache
from dataclasses import dataclass
from src.lib.geodesic import ground_distance
from src.core.custom_types import Geopoint_t
from src.core.singleton_metaclass import Singleton
from typing import List, Tuple

STOP_COMPLEX_OBJECT_TYPE = "CPLX"
STOP_OBJECT_TYPE = "STOP"


@dataclass(eq=False)
class StopComplex:
    """
    Holds general description of a stop complex. Doesnt hold it's stops.
    """
    stop_complex_id: int
    name: str
    town: str

    @property
    def readable_identifier(self):
        return f"{STOP_COMPLEX_OBJECT_TYPE}: {self.name} - {self.town} ({self.stop_complex_id})"

    def __str__(self):
        return f"Zespół: {self.name} ({self.town})"

    def __eq__(self, other):
        return self.stop_complex_id == other.stop_complex_id


@dataclass(eq=False)
class Stop:
    """
    Holds all information about a stop, such as it's street, number or geolocation.
    It can be optionally initialized with it's complex's name (defaults to None).
    """
    stop_id: int
    stop_number: str
    stop_complex_id: str
    latitude: float
    longitude: float
    street: str
    direction: str
    stop_complex_name: str
    complex_town: str

    def has_location(self):
        return not (self.longitude is None or self.latitude is None)

    def get_location(self) -> Geopoint_t:
        return (self.latitude, self.longitude)

    @property
    def readable_identifier(self):
        return f"{STOP_OBJECT_TYPE}: {self.stop_complex_name} {self.stop_number} - {self.street} w {self.complex_town} ({self.stop_id})"

    def __str__(self):
        text = (f"Przystanek: {self.stop_complex_name} {self.stop_number}").replace("Przystanek: N/A N/A", "Lokalizacja")
        return f"{text}"# w {self.complex_town}

    def __eq__(self, other):
        return self.stop_id == other.stop_id

    def __lt__(self, other):
        return self.stop_id < other.stop_id


class StopModel(DBModel, metaclass=Singleton):
    """
    Handles queries to the data base regarding Stops and Stop complexes. Provides cached access to all stops and complexes
    in the database.
    """

    def __init__(self) -> None:
        super().__init__()

        self._complexes_by_id = None
        self._stops_by_id = None

    def get_time_departures_from_stop_of_route(self, route, stop_id) -> list:
        sql_querry = f"""
        SELECT Departure_Time
        FROM Stop_Course
        WHERE STOP_ID = {stop_id} AND COURSE_ID = ANY(SELECT COURSE_ID
                                                    FROM Course
                                                    WHERE variant_id = {route.variant_id})"""

        return self._db.simple_type_mapping(sql_querry, str)

    def get_n_closest_stops(self, n: int, geopoint: Geopoint_t) -> List[Tuple[float, int]]:
        """
        :param n: how many stops to retrurn
        :param geopoint: (lat, lng) tuple
        :return: list of stop distances and ids
        """
        all_distances = sorted(
            [(ground_distance(geopoint, stop.get_location()), stop.stop_id) for stop in self.get_all_stops()])
        return all_distances[:n]

    @lru_cache(1)
    def get_complexes(self):
        sql = """
           select SC.STOP_COMPLEX_ID, SC.NAME, T.TOWN_NAME from STOP_COMPLEX SC inner join TOWN T on T.TOWN_ID = SC.TOWN_ID
            """
        all_complexes = self._db.simple_type_mapping(sql, StopComplex)
        self._complexes_by_id = {comp.stop_complex_id: comp for comp in all_complexes}
        return all_complexes

    @lru_cache(15, True)
    def get_stops_of_stop_complex(self, stop_complex_id):
        sql = f"""
            select ST.STOP_ID, ST.STOP_NUMBER, ST.STOP_COMPLEX_ID, ST.LATITUDE, ST.LONGITUDE, str_place.PLACE_NAME, dir_place.PLACE_NAME, SC.NAME, T.TOWN_NAME
            from STOP ST left join PLACE dir_place on dir_place.PLACE_ID = ST.DIRECTION 
            left join PLACE str_place on ST.STREET = str_place.PLACE_ID
            left join STOP_COMPLEX SC on ST.STOP_COMPLEX_ID = SC.STOP_COMPLEX_ID
            left join TOWN T on SC.TOWN_ID = T.TOWN_ID
            where  ST.STOP_COMPLEX_ID = {stop_complex_id}
            """
        return self._db.simple_type_mapping(sql, Stop)

    def get_complex_by_stop_id(self, stop_id):
        sql = f"""
            select SC.STOP_COMPLEX_ID, SC.NAME, T.TOWN_NAME from STOP_COMPLEX SC inner join TOWN T on T.TOWN_ID = SC.TOWN_ID
            where SC.STOP_COMPLEX_ID = (
                select STOP_COMPLEX_ID from STOP
                where STOP_ID = {stop_id}
            )
            """
        return self._db.simple_type_mapping(sql, StopComplex)[0]

    @staticmethod
    def parse_readable_identifier(readable_identifer: str):
        object_type = readable_identifer.split(":")[0]
        object_id = readable_identifer.split("(")[-1][:-1]
        return object_type, int(object_id)

    def get_complex_by_id(self, complex_id: int):
        if self._complexes_by_id is None:
            self.get_complexes()

        if complex_id in self._complexes_by_id:
            return self._complexes_by_id[complex_id]
        else:
            raise ValueError(f"Complex id {complex_id} not found")

    @lru_cache(1)
    def get_all_stops(self):
        sql = f"""
            select ST.STOP_ID, ST.STOP_NUMBER, ST.STOP_COMPLEX_ID, ST.LATITUDE, ST.LONGITUDE, str_place.PLACE_NAME, dir_place.PLACE_NAME, SC.NAME, T.TOWN_NAME
            from STOP ST left join PLACE dir_place on dir_place.PLACE_ID = ST.DIRECTION
            left join PLACE str_place on ST.STREET = str_place.PLACE_ID
            left join STOP_COMPLEX SC on ST.STOP_COMPLEX_ID = SC.STOP_COMPLEX_ID
            left join TOWN T on SC.TOWN_ID = T.TOWN_ID
            """

        stops = self._db.simple_type_mapping(sql, Stop)
        self._stops_by_id = {stop.stop_id: stop for stop in stops}
        return stops

    def get_stop_by_id(self, stop_id: int):
        if self._stops_by_id is None:
            self.get_all_stops()

        return self._stops_by_id[stop_id]
