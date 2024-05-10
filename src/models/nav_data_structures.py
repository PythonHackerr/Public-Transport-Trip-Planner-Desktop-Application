from dataclasses import dataclass

from src.core.custom_types import Seconds_t
from typing import List, Dict


@dataclass
class VariantStops:
    """What stops and in what order does this line variant stop at?"""
    variant_id: str
    ordered_stop_ids: List[int]


@dataclass
class SingleCourse:
    """Contains times of arrival on each stop of a line variant of a single vehicle assigned to course
    of some course_id"""
    course_id: str
    variant_stops: VariantStops  # Contains the info about the variant
    times_of_arrival_per_stop_id: Dict[int, Seconds_t]  # times of arrival on each stop of this course, key is stop_id

    def __lt__(self, other):
        return self.times_of_arrival_per_stop_id[self.variant_stops.ordered_stop_ids[0]] < \
            other.times_of_arrival_per_stop_id[other.variant_stops.ordered_stop_ids[0]]
