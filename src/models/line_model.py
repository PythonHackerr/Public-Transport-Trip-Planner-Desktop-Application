from src.core.model import DBModel, Model
from dataclasses import dataclass
from src.models.stop_model import Stop, StopModel
from src.models.nav_data_structures import VariantStops
from src.core.singleton_metaclass import Singleton
import logging
from PySide6.QtCore import QThread

@dataclass(eq=False)
class StopCourseTime:
    """UNUSED RIGHT NOW"""
    line: str
    course_id: str
    stop_id: Stop
    day_type: str
    time: str



class Route_Complex():
    def __init__(self, line_number, variant_id, variant_name):
        self._line_number = line_number
        self._variant_id = variant_id
        self._variant_name = variant_name

    @property
    def line_number(self):
        return self._line_number

    @property
    def variant_id(self):
        return self._variant_id

    @property
    def variant_name(self):
        return self._variant_name


class Variant_Stops():
    def __init__(self, variant_id, stop_id):
        self._variant_id = variant_id
        self._stop_id = stop_id

    @property
    def variant_id(self):
        return self._variant_id

    @property
    def stop_id(self):
        return self._stop_id



class Route(DBModel):
    def __init__(self, line_number, variant_id, variant_name, destination):
        super().__init__()
        self._line_number = line_number
        self._variant_id = variant_id
        self._variant_name = variant_name
        self._destination = destination
        self._stop_model = StopModel()
        self._stops = self._get_stops_of_route()

    def _get_stops_of_route(self) -> list:
        stops = []
        sql_querry = f"""
        SELECT stop_id
        FROM STOP_VARIANT
        WHERE variant_id = '{self._variant_id}'
        """
        data = self._db.simple_type_mapping(sql_querry, int)
        for stop_id in data:
            stops.append(self._stop_model.get_stop_by_id(stop_id))
        return stops


    @property
    def line_number(self):
        return self._line_number

    @property
    def variant_id(self):
        return self._variant_id

    @property
    def variant_name(self):
        return self._variant_name

    @property
    def destination(self):
        return self._destination

    @property
    def stops(self):
        return self._stops


    def get_time_departures_from_stop(self, stop: Stop) -> list:
        sql_querry = f"""SELECT Time FROM Stop_Course
        WHERE Line = '{self.line_number}' AND Course_Id LIKE "{self.variant_id}/%' AND Day_type = 'DP' AND STOP_ID = {stop.stop_id}"""

        return self._db.simple_type_mapping(sql_querry, str)

    @property
    def line_number(self):
        return self._line_number

    @property
    def variant_id(self):
        return self._variant_id

    @property
    def destination(self):
        return self._destination

    @property
    def stops(self):
        return self._stops

    def __str__(self) -> str:
        return f"{self.line_number} -> {self.destination}"


class NavRoute():
    def __init__(self, start_stop_id, destination_stop_id):
        self._start_stop_id = start_stop_id
        self._destination_stop_id = destination_stop_id

    @property
    def start_stop_id(self):
        return self._start_stop_id

    @property
    def destination_stop_id(self):
        return self._destination_stop_id



class LineComplex:
    def __init__(self, line_complex_id: int):
        self._line_complex_id = line_complex_id

    @property
    def line_complex_id(self):
        return self._line_complex_id

    def __str__(self):
        return f"{self._line_complex_id}"


class Line:
    def __init__(self, line_id, line_type_id) -> None:
        self._line_id = line_id
        self._line_type_id = line_type_id
        self._variants = None

    @property
    def line_id(self):
        return self._line_id

    @property
    def line_type_id(self):
        return self._line_type_id

    @property
    def variants(self):
        return self._variants

    def _create_routes(self, routes) -> list:
        all_routes = []
        for varaint_id, varaint_name, destination in routes:
            all_routes.append(Route(self.line_id, varaint_id, varaint_name, destination))
        self._variants = all_routes
        return all_routes



class Destination:
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self):
        return self._name



class Line_type:
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self):
        return self._name


class LineModel(DBModel, metaclass=Singleton):
    def __init__(self) -> None:
        super().__init__()
        self._lines_complex = None
        self._lines_routes = None
        self._lines = None
        self.all_lines_routes = None


    def get_variant_stops(self, variant_id):
        if (self.all_lines_routes is None):
            self.all_lines_routes = self._get_all_lines_routes()
        return VariantStops (
                            variant_id,
                            self.all_lines_routes[variant_id]
                            )


    def _get_all_lines_routes(self):
        variant_stops_dict = {}
        sql = f"""
            select VARIANT_ID, STOP_ID from STOP_VARIANT
            """
        variant_stops = self._db.simple_type_mapping(sql, Variant_Stops)

        for vs in variant_stops:
            if (vs.variant_id in variant_stops_dict):
                variant_stops_dict[vs.variant_id].append(vs.stop_id)
            else:
                variant_stops_dict[vs.variant_id] = [vs.stop_id]
        return variant_stops_dict


    def _get_line_routes(self, line_id):
        line_routes = []
        route_types = []
        sql = f"""
            SELECT v.line_id, v.variant_id, v.variant_name
            FROM VARIANT v
            WHERE line_id = '{line_id}'  and (Select v2.is_basic
                                    FROM VARIANT v2
                                    WHERE v2.variant_id = v.variant_id) = 1
            """
        routes_complex = self._db.simple_type_mapping(sql, Route_Complex)

        for route_complex in routes_complex:
            route_type = self._get_line_type_by_variant_id(route_complex.variant_id).name
            route = Route(route_complex.line_number, route_complex.variant_id, route_complex.variant_name, None)
            last_stop = route._stops[-1:][0]
            sql = f"""
            SELECT name
            FROM STOP_COMPLEX sc
            WHERE sc.stop_complex_id = {last_stop.stop_complex_id}
            UNION
            SELECT stop_number
            from STOP s
            WHERE s.stop_id = {last_stop.stop_id}
            """
            destination = self._db.simple_type_mapping(sql, Destination)
            route._destination = destination
            line_routes.append(route)
            route_types.append(route_type)

        return line_routes, route_types

    def _get_stops_of_route(self, variant_id) -> list:
        self._stop_model = StopModel()
        stops = []
        sql_querry = f"""
        SELECT stop_id
        FROM STOP_VARIANT
        WHERE variant_id = '{variant_id}'
        """
        data = self._db.simple_type_mapping(sql_querry, int)
        for stop_id in data:
            stops.append(self._stop_model.get_stop_by_id(stop_id))
        self._stops = stops
        return stops

    def _get_line_type_by_variant_id(self, variant_id):
        sql_querry = f"""
        SELECT type_name
        FROM LINE_TYPE
        WHERE type_id = (
            SELECT LINE_TYPE_ID 
            FROM LINE 
            WHERE LINE_ID = (
                SELECT LINE_ID
                FROM VARIANT
                WHERE Variant_id = {variant_id}
            )
        )
        """
        line_type = self._db.simple_type_mapping(sql_querry, Line_type)[0]
        return line_type


    def _get_line_type_by_type_id(self, type_id):
        sql_querry = f"""
        SELECT type_name
        FROM LINE_TYPE
        WHERE type_id = {type_id}
        """
        line_type = self._db.simple_type_mapping(sql_querry, Line_type)[0]
        return line_type


    def _get_line_by_variant_id(self, variant_id):
        sql_querry = f"""
        SELECT LINE_ID
        FROM VARIANT
        WHERE Variant_id = {variant_id}
        """
        line_type = self._db.simple_type_mapping(sql_querry, Line_type)[0]
        return line_type
        


    def _get_all_lines(self):
        sql = f"""
        SELECT  *
        FROM LINE l
        """
        all_lines = self._db.simple_type_mapping(sql, Line)
        return all_lines


    @property
    def lines(self):
        return self._lines