import logging
from src.core.model import DBModel
from src.models.nav_data_structures import SingleCourse
from src.models.stop_model import StopModel
from src.models.line_model import LineModel
from src.core.custom_types import *
from src.core.singleton_metaclass import Singleton
from math import floor

SPACE_CHUNK_COUNT = 32
TIME_CHUNK_COUNT = 32


class NavDataModel(DBModel, metaclass=Singleton):
    def __init__(self, stop_model, line_model):
        super().__init__()
        self._stop_model: StopModel = stop_model
        self._lines_model: LineModel = line_model
        self.get_stop_by_id = self._stop_model.get_stop_by_id
        self.get_n_closest_stops = self._stop_model.get_n_closest_stops

    @staticmethod
    def get_chunk_from_location_and_time(location: Geopoint_t, time: Seconds_t) -> int:
        """
        Returns the spacetime chunk of some location and time. Each chunk id consists of:
         - first 5 bits representing latitude chunk
         - second 5 bits representing longitude chunk
         - last 5 bits represent time chunk

        :param location: Geopoint_t tuple
        :param time: time in seconds
        :return: chunk id
        """
        lat, lng = location
        lat_c = floor((lat - 51.921869) / 0.561141 * SPACE_CHUNK_COUNT)
        lng_c = floor((lng - 20.462591) / 1.001192 * SPACE_CHUNK_COUNT)
        time_c = floor(time / 60 / 1777 * TIME_CHUNK_COUNT)
        return ((lat_c) * SPACE_CHUNK_COUNT + lng_c) * TIME_CHUNK_COUNT + time_c

    @staticmethod
    def next_chronologically_chunk(chunk: int):
        return (chunk & 0b111111111100000) + ((chunk + 1) & 0b11111)

    def update_graph_here_now(self, nav_graph: "NavGraph", chunk: int, excluded_chunks: Optional[list[int]] = None):
        """
        Download and update graph when new chunk is visited
        :param excluded_chunks: what chunks have already been downloaded?
        :param chunk: which chunk to insert?
        :param nav_graph: Graph of navigation nodes to inject the chunk to
        """

        lat_chunk = chunk >> 10
        lng_chunk = (chunk >> 5) & 0b11111
        time_chunk = chunk & 0b11111

        logging.info(f"Dowloading space time chunk {lat_chunk} x {lng_chunk} @ {time_chunk}")

        if excluded_chunks is None or len(excluded_chunks) == 0:
            excluded_chunks = [-1]

        # Update courses
        sql_query = f"""
        -- get all full courses that have at least one of their departures in this space time chunk
        select SC.STOP_ID, SC.COURSE_ID, SC.DEPARTURE_TIME, CO.VARIANT_ID
        from STOP_COURSE SC inner join (
            select SC.COURSE_ID from STOP_COURSE SC
            where SC.CHUNK = {chunk}
            minus
            select SC.COURSE_ID from STOP_COURSE SC
            where SC.CHUNK in ({",".join(map(str, excluded_chunks))})
        ) SUB on SUB.COURSE_ID = SC.COURSE_ID inner join COURSE CO on CO.COURSE_ID = SC.COURSE_ID
    """
        cur = self._db.cursor.execute(sql_query)
        logging.info("Courses cursor created")
        all_new_courses: dict[str, SingleCourse] = dict()
        i = 0
        for stop_id, course_id, departure_time, variant_id in cur.fetchall():
            i += 1
            if course_id not in all_new_courses:
                variant_stops = self._lines_model.get_variant_stops(variant_id)
                all_new_courses[course_id] = SingleCourse(course_id, variant_stops, dict())
            all_new_courses[course_id].times_of_arrival_per_stop_id[stop_id] = departure_time * 60
        logging.info(f"Downloaded total of {i} arrival times in {len(all_new_courses)} courses")
        # Apply downloaded courses
        for course in all_new_courses.values():
            # !!! there is a chance of downloading the same course multiple times!
            if course.variant_stops.ordered_stop_ids[0] in course.times_of_arrival_per_stop_id:
                nav_graph.add_course_to_graph(course)
            else:
                logging.warning(f"Course {course.course_id} variant doesnt match course")

        sql_query = f"""
    select STOP_ID, NEIGHBOUR_ID, DISTANCE
    from STOP_NEIGHBOUR
    where STOP_ID in (
                select subS.STOP_ID
                  from STOP subS
                  where floor((subS.LATITUDE - 51.921869) / 0.561141 * {SPACE_CHUNK_COUNT}) = {lat_chunk}
                    and floor((subS.LONGITUDE - 20.462591) / 1.001192 * {SPACE_CHUNK_COUNT}) = {lng_chunk})
    """
        cur = self._db.cursor.execute(sql_query)
        logging.info("Neighbour cursor created")
        for stop_id, neighbour_id, distance in cur:
            nav_graph.get_nav_node(stop_id).neighbours.append((distance, neighbour_id))
        logging.info(f"{lat_chunk} x {lng_chunk} @ {time_chunk} chunk data insertion complete")
