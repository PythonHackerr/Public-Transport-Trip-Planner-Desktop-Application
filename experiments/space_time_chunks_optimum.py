import logging
import time
from math import floor

from src.models.line_model import LineModel
from src.models.nav_data_model import NavDataModel
from src.lib.navigation_graph import NavGraph
from src.core.custom_types import *
from src.models.nav_data_structures import SingleCourse
from src.models.stop_model import StopModel


class Timer:
    def __init__(self):
        self._start_times = []
        self._prompts = []

    def start(self, prompt: str):
        self._prompts.append(prompt)
        self._start_times.append(time.time())

    def end(self):
        tab = '\t'
        logging.info(
            f"{tab * len(self._prompts)} {self._prompts[-1]} execution time: {(time.time() - self._start_times[-1]) * 1000}ms")
        self._start_times.pop()
        self._prompts.pop()


TIMER = Timer()


class SpaceChunkOnly(NavDataModel):
    def __init__(self, n_of_chunks: int):
        TIMER.start("Init data model")
        super().__init__()
        TIMER.end()
        self._chunk_count = n_of_chunks

    def update_graph_here_now(self, nav_graph: "NavGraph", chunk: tuple[int, int]):
        """
        Download and update graph when new chunk is visited
        :param chunk: which chunk to insert?
        :param nav_graph: Graph of navigation nodes to inject the chunk to
        """
        # lat_chunk, lng_chunk, time_chunk = chunk
        lat_chunk, lng_chunk = chunk

        TIMER.start("Course cursor creation")
        # Update courses
        sql_query = f"""
            -- select data of entire courses that match the criteria
            select SC.STOP_ID, SC.COURSE_ID, SC.DEPARTURE_TIME, CO.VARIANT_ID
            from STOP_COURSE SC inner join COURSE CO on CO.COURSE_ID = SC.COURSE_ID
            -- only accept courses that happen after this time but in this chunk
              where CO.VARIANT_ID in (
                -- only accept courses of variants that have stops in this space chunk
                select distinct VARIANT_ID
                from STOP_VARIANT
                where STOP_ID in (
                    select subS.STOP_ID
                      from STOP subS
                      where floor((subS.LATITUDE - 51.921869) / 0.561141 * {self._chunk_count}) = {lat_chunk}
                        and floor((subS.LONGITUDE - 20.462591) / 1.001192 * {self._chunk_count}) = {lng_chunk}))
        """
        cur = self._db.cursor.execute(sql_query)
        TIMER.end()
        TIMER.start("Overall course download")
        TIMER.start("Download courses")
        all_new_courses: dict[str, SingleCourse] = dict()
        i = 0
        for stop_id, course_id, departure_time, variant_id in cur:
            i += 1
            if i % 10000 == 0:
                logging.info(f"Applied {i} arrival times on {len(all_new_courses)} courses")
            if course_id not in all_new_courses:
                variant_stops = self._lines_model.get_variant_stops(variant_id)
                all_new_courses[course_id] = SingleCourse(course_id, variant_stops, dict())
            all_new_courses[course_id].times_of_arrival_per_stop_id[stop_id] = departure_time * 60
        logging.info(f"total arrival times: {i}")
        TIMER.end()
        TIMER.start("Apply new courses")
        # Apply downloaded courses
        for course in all_new_courses.values():
            # !!! SOME COURSES WILL NBE DOWNLOADED MULTIPLE TIMES WHEN THEY STICK OUTSIDE THE SPACE-TIME CHUNK
            nav_graph.add_course_to_graph(course)
        TIMER.end()
        TIMER.end()
        TIMER.start("Neighbour cursor creation")
        sql_query = f"""
        select STOP_ID, NEIGHBOUR_ID, DISTANCE
        from STOP_NEIGHBOUR
        where STOP_ID in (
                    select subS.STOP_ID
                      from STOP subS
                      where floor((subS.LATITUDE - 51.921869) / 0.561141 * {self._chunk_count}) = {lat_chunk}
                        and floor((subS.LONGITUDE - 20.462591) / 1.001192 * {self._chunk_count}) = {lng_chunk})
        """
        cur = self._db.cursor.execute(sql_query)
        TIMER.end()
        TIMER.start("Apply neighbours")
        for stop_id, neighbour_id, distance in cur:
            nav_graph.get_nav_node(stop_id).neighbours.append((distance, neighbour_id))
        TIMER.end()
        logging.info("Chunk data insertion complete")

    def run_this_model(self, chunk):
        g = NavGraph(self)
        self.update_graph_here_now(g, chunk)


class SpaceTimeChunks(NavDataModel):
    def __init__(self, stop_model, line_model, n_of_chunks: int, n_of_time_chunks: int):
        TIMER.start("Init data model")
        super().__init__(stop_model, line_model)
        TIMER.end()
        self._chunk_count = n_of_chunks
        self._time_chunk_count = n_of_time_chunks

    def update_graph_here_now(self, nav_graph: "NavGraph", chunk: tuple[int, int, int]):
        """
        Download and update graph when new chunk is visited
        :param chunk: which chunk to insert?
        :param nav_graph: Graph of navigation nodes to inject the chunk to
        """
        # lat_chunk, lng_chunk, time_chunk = chunk
        lat_chunk, lng_chunk, time_chunk = chunk

        TIMER.start("Overall course download")
        TIMER.start("Course cursor creation")
        # Update courses
        sql_query = f"""
            -- select data of entire courses that match the criteria
            select SC.STOP_ID, SC.COURSE_ID, SC.DEPARTURE_TIME, CO.VARIANT_ID from STOP_COURSE SC inner join COURSE CO on SC.COURSE_ID = CO.COURSE_ID inner join (
                select distinct SC.COURSE_ID
                from STOP_COURSE SC
                         inner join COURSE CO on CO.COURSE_ID = SC.COURSE_ID
                where CO.VARIANT_ID in (
                    -- only accept courses of variants that have stops in this space chunk
                    select distinct VARIANT_ID
                    from STOP_VARIANT
                    where STOP_ID in (
                        select subS.STOP_ID
                          from STOP subS
                          where floor((subS.LATITUDE - 51.921869) / 0.561141 * {self._chunk_count}) = {lat_chunk}
                            and floor((subS.LONGITUDE - 20.462591) / 1.001192 * {self._chunk_count}) = {lng_chunk}
                        )
                        -- only accept courses that happen in this time chunk
                    ) and floor(SC.DEPARTURE_TIME / 1777 * {self._time_chunk_count}) = {time_chunk}
            ) SUB on SUB.COURSE_ID = SC.COURSE_ID
        """
        cur = self._db.cursor.execute(sql_query)
        TIMER.end()
        TIMER.start("Download courses")
        all_new_courses: dict[str, SingleCourse] = dict()
        i = 0
        for stop_id, course_id, departure_time, variant_id in cur:
            i += 1
            if i % 1000 == 0:
                TIMER.start(f"Time of creating {i}th dep. time")
            if course_id not in all_new_courses:
                variant_stops = self._lines_model.get_variant_stops(variant_id)
                all_new_courses[course_id] = SingleCourse(course_id, variant_stops, dict())
            all_new_courses[course_id].times_of_arrival_per_stop_id[stop_id] = departure_time * 60
            if i % 1000 == 0:
                TIMER.end()
        TIMER.end()
        TIMER.start("Apply new courses")
        # Apply downloaded courses
        for course in all_new_courses.values():
            # !!! SOME COURSES WILL NBE DOWNLOADED MULTIPLE TIMES WHEN THEY STICK OUTSIDE THE SPACE-TIME CHUNK
            nav_graph.add_course_to_graph(course)
        TIMER.end()
        TIMER.end()
        TIMER.start("Neighbour cursor creation")
        sql_query = f"""
        select STOP_ID, NEIGHBOUR_ID, DISTANCE
        from STOP_NEIGHBOUR
        where STOP_ID in (
                    select subS.STOP_ID
                      from STOP subS
                      where floor((subS.LATITUDE - 51.921869) / 0.561141 * {self._chunk_count}) = {lat_chunk}
                        and floor((subS.LONGITUDE - 20.462591) / 1.001192 * {self._chunk_count}) = {lng_chunk})
        """
        cur = self._db.cursor.execute(sql_query)
        TIMER.end()
        TIMER.start("Apply neighbours")
        for stop_id, neighbour_id, distance in cur:
            nav_graph.get_nav_node(stop_id).neighbours.append((distance, neighbour_id))
        TIMER.end()
        logging.info("Chunk data insertion complete")

    def run_this_model(self, chunk):
        g = NavGraph(self)
        self.update_graph_here_now(g, chunk)


def test_space_chunkers():
    counts = [50, 100, 125, 150]

    for chunk_count in counts:
        logging.info(f"{chunk_count} --------------------------------")
        TIMER.start(f"{chunk_count}x{chunk_count} space only")
        experiment = SpaceChunkOnly(chunk_count)
        experiment.run_this_model((chunk_count // 2, chunk_count // 2))
        TIMER.end()


def test_space_time_chunking():
    counts = [
        (32, 32),
        (64, 32),
        (100, 32),
        (150, 32),
    ]

    stop_model = StopModel()
    stop_model.get_all_stops()
    line_model = LineModel()

    for chunk_count, time_chunks in counts:
        logging.info(f"{chunk_count} @ {time_chunks} --------------------------------")
        TIMER.start(f"{chunk_count}x{chunk_count} @ {time_chunks}")
        experiment = SpaceTimeChunks(stop_model, line_model, chunk_count, time_chunks)
        experiment.run_this_model((chunk_count // 2, chunk_count // 2, floor(time_chunks * 16 / 24)))
        TIMER.end()


def main():
    logging.basicConfig(format="[%(asctime)s->%(levelname)s->%(module)s" +
                               "->%(funcName)s]: %(message)s",
                        datefmt="%H:%M:%S",
                        level=logging.INFO)

    test_space_time_chunking()


if __name__ == "__main__":
    main()
