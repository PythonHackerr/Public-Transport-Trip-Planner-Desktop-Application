import logging
import math
from dataclasses import dataclass
from src.core.custom_types import Geopoint_t
from src.models.nav_data_model import NavDataModel
from src.models.nav_data_structures import SingleCourse
from src.models.stop_model import Stop
from typing import Optional


@dataclass
class TransitNetworkNode:
    """Transit stop navigation node, holds information about the stop, the next stops for each line that goes through it
    and it's neighbours"""
    stop: Stop
    line_variant_courses: dict[str, list[SingleCourse]]
    """COURSE LISTS MUST BE SORTED BY TIME!!"""
    neighbours: list[tuple[float, int]]
    """list of stop_ids (int) in walking range and their distance (float)"""
    _ordered: bool = True
    """Are variant courses sorted by time?"""

    def find_soonest_course_of_variant_on_this_stop(self, actual_time_of_arrival: float,
                                                    line_variant: str) -> Optional[SingleCourse]:
        """
        Does a bin search on all courses of a given variant to determine which one arrives the fastest
        :param actual_time_of_arrival: minimum time of arrival of the next course
        :param line_variant: which variant to consider
        :return: the soonest valid course
        """
        if not self._ordered:
            raise Exception("Binary search wont work on unsorted data!")
        valid_courses = self.line_variant_courses[line_variant]

        if self.stop.stop_id not in valid_courses[-1].times_of_arrival_per_stop_id:
            logging.info("Natrafiono na kwiatek")
            return None

        # All courses have already sailed!
        if valid_courses[-1].times_of_arrival_per_stop_id[self.stop.stop_id] <= actual_time_of_arrival or len(
                valid_courses) == 0:
            return None

        bin_left = 0
        bin_right = len(valid_courses) - 1
        # bin search
        while bin_left + 1 < bin_right:
            bin_index = math.ceil((bin_left + bin_right) / 2)
            if valid_courses[bin_index].times_of_arrival_per_stop_id[self.stop.stop_id] > actual_time_of_arrival:
                bin_right = bin_index
            else:
                bin_left = bin_index

        if valid_courses[bin_left].times_of_arrival_per_stop_id[self.stop.stop_id] > actual_time_of_arrival:
            return valid_courses[bin_left]
        else:
            return valid_courses[bin_right]

    def add_course(self, course: SingleCourse):
        self._ordered = False
        if course.variant_stops.variant_id not in self.line_variant_courses:
            self.line_variant_courses[course.variant_stops.variant_id] = [course]
        else:
            self.line_variant_courses[course.variant_stops.variant_id].append(course)

    def order_courses(self):
        self._ordered = True
        for variant in self.line_variant_courses:
            self.line_variant_courses[variant] = sorted(self.line_variant_courses[variant])

    def __hash__(self):
        return hash(self.stop.stop_id)

    def __eq__(self, other: "TransitNetworkNode"):
        return self.stop == other.stop

    def __lt__(self, other):
        return self.stop < other.stop

    def __str__(self):
        return f"Transit node {self.stop.readable_identifier}"


class FakeStop(Stop):
    """
    Represents a fake stop used in fake stop nodes
    """

    def __init__(self, fake_id: int, fake_name: str, location: Geopoint_t):
        super().__init__(fake_id, "", "", location[0], location[1], "", "", fake_name, "")


class FakeNetworkNode(TransitNetworkNode):
    """
    If user starts their travel from an arbitrary point, this location is added to the graph as a FakeStopNode
    """

    def __init__(self,
                 fake_id: int,
                 fake_name: str,
                 location: Geopoint_t,
                 neighbours: list[tuple[float, int]]):
        self.stop = FakeStop(fake_id, fake_name, location)
        self.neighbours = neighbours
        self.line_variant_courses = {}


class NavGraph:
    def __init__(self, nav_data_model: NavDataModel = None):
        self._hits = 0
        self._misses = 0
        self._nav_data_model: NavDataModel = nav_data_model
        self._graph: dict[int, TransitNetworkNode] = {}
        self._courses_present_in_graph = set()

    @property
    def courses_present_in_graph(self):
        return self._courses_present_in_graph

    def stop_id_present(self, node_id: int):
        return node_id in self._graph

    def add_node(self, node: TransitNetworkNode):
        self._graph[node.stop.stop_id] = node

    def get_nav_node(self, stop_id: int) -> TransitNetworkNode:
        if stop_id not in self._graph:
            # If this node isn't in the graph yet, make its ghost. If you step into the ghost, download its contents
            if self._nav_data_model is not None:
                self._graph[stop_id] = TransitNetworkNode(self._nav_data_model.get_stop_by_id(stop_id), {}, [])
            else:
                raise Exception("Cant create an empty node! (No stop model provided)")
        return self._graph[stop_id]

    def add_course_to_graph(self, course: SingleCourse):
        affected_nodes = set()
        if course.course_id not in self._courses_present_in_graph:
            self._hits += 1
            self._courses_present_in_graph.add(course.course_id)
            for stop_id in course.variant_stops.ordered_stop_ids:
                self.get_nav_node(stop_id).add_course(course)
                affected_nodes.add(stop_id)

            for stop_id in affected_nodes:
                self.get_nav_node(stop_id).order_courses()
        else:
            self._misses += 1

    def remove_node(self, stop_id: int):
        self._graph.pop(stop_id)
