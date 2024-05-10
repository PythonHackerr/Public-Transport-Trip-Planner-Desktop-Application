import logging
import math
from queue import PriorityQueue
from src.lib.geodesic import ground_distance
from src.lib.navigation_graph import TransitNetworkNode, FakeNetworkNode, NavGraph
from src.lib.navigation_steps import NavStep, TakeTransit, GoOnFoot, StartAtNode
from src.core.custom_types import *
from src.models.nav_data_model import NavDataModel
from queue import Queue

SECONDS_IN_A_DAY = 24 * 3600

# --- TIME IN SECONDS, SPEED IN METERS PER SECOND, DISTANCE IN METERS
AVG_HUMAN_WALKING_SPEED = 1.0
HEURISTIC_STRAIGHT_LINE_SPEED = 5.0
BASE_WALK_TIME: Seconds_t = 5.0
MINIMUM_VARIANT_SWITCHING_TIME: Seconds_t = 15.0  # minimum time for switching lines on a stop

FAKE_START_ID = -1
FAKE_DESTINATION_ID = -2
WALKED_LINE_VARIANT = "walked"
MINIMUM_STOPS_IN_RANGE = 6

EXCLUDE_LAST_N_CHUNKS = 500

DOWNLOAD_PATH_FINDS = 3
FINE_TUNE_PATH_FINDS = 15
DOWNLOAD_PATIENCE = 2000
FINE_TUNE_PATIENCE = 50000


class NavRouteQueue(PriorityQueue):
    """Custom put method for the queue"""

    def put(self, heuristic_time: Seconds_t, actual_time_of_arrival: Seconds_t, last_variant_id: Optional[str],
            next_node: TransitNetworkNode) -> None:
        item = (heuristic_time, actual_time_of_arrival, last_variant_id, next_node)
        super().put(item)

    def get(self) -> tuple[Seconds_t, Seconds_t, str, TransitNetworkNode]:
        return super().get()


class AStarNav:
    def __init__(self, nav_data_model: NavDataModel = None):
        self._nav_data_model: NavDataModel = nav_data_model

        self._graph = NavGraph(self._nav_data_model)
        self._chunks: set[int] = set()  # Which chunks are currently in memory?
        self._chunk_queue: Queue[int] = Queue()  # last N chunks to exclude from download

        self._min_arrival_time: dict[int, Seconds_t] = {}  # WHEN will I optimally get here?
        self._min_path_taken: dict[int, NavStep] = {}  # HOW  will I optimally get here?

    @property
    def graph(self):
        return self._graph

    @staticmethod
    def heura(p1: Geopoint_t, p2: Geopoint_t, time_taken_so_far: Seconds_t) -> Seconds_t:
        """
        Heuristic time of travel between 2 points
        :param p1: first point
        :param p2: second point
        :param time_taken_so_far: how much time did it take to get to the first point?
        :return: heuristic total time
        """
        return ground_distance(p1, p2) / HEURISTIC_STRAIGHT_LINE_SPEED + time_taken_so_far

    def patience_drop_off(self, base: int, horizon: int, x: int):
        return round(base * (1 - 1 / horizon) ** x)

    def _init_A_star(self,
                     starting_time: Seconds_t,
                     start_node: TransitNetworkNode,
                     destination_node: TransitNetworkNode):
        """
        Initializes A* algorithm, fills _min_arival_time and _min_path_taken with data
        :param starting_time: time of the start of the journey
        :param start_node: nav node algorithm should start at
        :param destination_node: nav node algorith should end at
        :return:
        """

        queue = NavRouteQueue()
        self._min_arrival_time = {}
        self._min_path_taken = {}

        self._min_path_taken[start_node.stop.stop_id] = StartAtNode(start_node, starting_time)
        self._min_arrival_time[start_node.stop.stop_id] = starting_time

        time_walked_from_start_to_dest = ground_distance(start_node.stop.get_location(),
                                                         destination_node.stop.get_location()) / AVG_HUMAN_WALKING_SPEED
        self._min_path_taken[destination_node.stop.stop_id] = GoOnFoot(start_node, destination_node, starting_time,
                                                                       starting_time + time_walked_from_start_to_dest)
        self._min_arrival_time[destination_node.stop.stop_id] = starting_time + time_walked_from_start_to_dest

        start_geopoint = start_node.stop.get_location()
        destination_geopoint = destination_node.stop.get_location()

        initial_heuristic = self.heura(start_geopoint, destination_geopoint, 0)
        queue.put(initial_heuristic, starting_time, None, start_node)

        # Debug info ----

        iterations_per_reach = dict()
        total_times_destination_reached = 0

        # ---------------

        total_iterations = 0
        iteration_limit = 1e6
        n_times_dest_reached = 0
        while not queue.qsize() == 0 and iteration_limit > total_iterations and n_times_dest_reached < DOWNLOAD_PATH_FINDS + FINE_TUNE_PATH_FINDS:
            heuristic_time, actual_time_of_arrival, last_variant_id, current_node = queue.get()

            total_iterations += 1
            # iterations ended for download path finds, proceed with fine-tuning
            if not iteration_limit > total_iterations and n_times_dest_reached < DOWNLOAD_PATH_FINDS:
                logging.info("Downloads ended prematurely due to insufficient iterations, begin fine-tuning path")
                n_times_dest_reached = DOWNLOAD_PATH_FINDS
                iteration_limit = self.patience_drop_off(FINE_TUNE_PATIENCE, FINE_TUNE_PATH_FINDS,
                                                         n_times_dest_reached - DOWNLOAD_PATH_FINDS)

            # Some other path to this node was better? Ignore this path
            if current_node.stop.stop_id not in self._min_arrival_time:
                self._min_arrival_time[current_node.stop.stop_id] = math.inf
            elif self._min_arrival_time[current_node.stop.stop_id] < actual_time_of_arrival or actual_time_of_arrival > \
                    self._min_arrival_time[destination_node.stop.stop_id]:
                continue

            # --- Terminal condition ---
            # The first time you reach a destination node will probably not be the best one.
            # try reaching it N times with some degree of patience, maybe you will find something better
            if current_node == destination_node:
                logging.info(f"DESTINATION REACHED {n_times_dest_reached + 1} TIMES")
                iterations_per_reach[n_times_dest_reached + 1] = total_iterations
                total_iterations = 0
                # Download stage
                if n_times_dest_reached < DOWNLOAD_PATH_FINDS - 1:
                    iteration_limit = self.patience_drop_off(DOWNLOAD_PATIENCE, DOWNLOAD_PATH_FINDS,
                                                             n_times_dest_reached)
                # Fine tune stage
                else:
                    iteration_limit = self.patience_drop_off(FINE_TUNE_PATIENCE, FINE_TUNE_PATH_FINDS,
                                                             n_times_dest_reached - DOWNLOAD_PATH_FINDS)
                if n_times_dest_reached == DOWNLOAD_PATH_FINDS - 1:
                    logging.info("Fine tuning shortest path")
                n_times_dest_reached += 1
                continue

            # --- Download a new chunk if its not present in the graph ---
            # Download this one and chronologically next one. It ensures the algorithm can consider waiting
            # on a stop for 1 to 2 hours at most.
            # Don't download in fine-tuning stage.
            if self._nav_data_model is not None and n_times_dest_reached < DOWNLOAD_PATH_FINDS:
                current_chunk = self._nav_data_model.get_chunk_from_location_and_time(current_node.stop.get_location(),
                                                                                      actual_time_of_arrival)
                if current_chunk not in self._chunks:
                    self._nav_data_model.update_graph_here_now(self._graph, current_chunk,
                                                               list(self._chunk_queue.queue))
                    self._chunk_queue.put(current_chunk)
                    if self._chunk_queue.qsize() > EXCLUDE_LAST_N_CHUNKS:
                        self._chunk_queue.get()
                    self._chunks.add(current_chunk)

                # Broaden the scope of search
                next_chunk = self._nav_data_model.next_chronologically_chunk(current_chunk)
                if next_chunk not in self._chunks:
                    self._nav_data_model.update_graph_here_now(self._graph, next_chunk,
                                                               list(self._chunk_queue.queue))
                    self._chunk_queue.put(next_chunk)
                    if self._chunk_queue.qsize() > EXCLUDE_LAST_N_CHUNKS:
                        self._chunk_queue.get()
                    self._chunks.add(next_chunk)

            # --- consider switching to a different line ---
            actual_time_of_arrival += MINIMUM_VARIANT_SWITCHING_TIME
            for line_variant in current_node.line_variant_courses:
                if last_variant_id is None or line_variant != last_variant_id:
                    # for each variant on this stop assuming it's not the one we have already stepped off of
                    next_course = current_node.find_soonest_course_of_variant_on_this_stop(actual_time_of_arrival,
                                                                                           line_variant)
                    if next_course is None:
                        continue
                    next_course_departure_time = next_course.times_of_arrival_per_stop_id[current_node.stop.stop_id]
                    n_of_stops_in_variant = len(next_course.variant_stops.ordered_stop_ids)
                    # take the next vehicle that comes and try going to all its next stops
                    for i in range(n_of_stops_in_variant - 1, 0, -1):
                        next_stop_id = next_course.variant_stops.ordered_stop_ids[i]
                        if next_stop_id == current_node.stop.stop_id:
                            # when iterating backwards, we eventually encounter the stop we have started at, break
                            break
                        # otherwise, add it to the queue
                        next_stop_node = self._graph.get_nav_node(next_stop_id)
                        next_actual_time = next_course.times_of_arrival_per_stop_id[next_stop_id]
                        total_time = next_actual_time - actual_time_of_arrival
                        next_heuristic_time = self.heura(
                            destination_geopoint,
                            next_stop_node.stop.get_location(),
                            total_time)
                        # Put it all together
                        if next_stop_id not in self._min_arrival_time or next_actual_time < self._min_arrival_time[
                            next_stop_id]:
                            self._min_arrival_time[next_stop_id] = next_actual_time
                            self._min_path_taken[next_stop_id] = TakeTransit(
                                current_node,
                                next_stop_node,
                                next_course_departure_time,
                                next_actual_time,
                                line_variant)
                            queue.put(next_heuristic_time, next_actual_time, line_variant, next_stop_node)
                        elif next_stop_node == destination_node:
                            total_times_destination_reached += 1

            # --- consider walking to a different stop ---
            for distance, neighbour_id in current_node.neighbours:
                next_stop_node = self._graph.get_nav_node(neighbour_id)
                next_stop_id = next_stop_node.stop.stop_id
                time_walked_to_neighbour = distance / AVG_HUMAN_WALKING_SPEED + BASE_WALK_TIME
                next_actual_time = actual_time_of_arrival + time_walked_to_neighbour
                total_time = next_actual_time - actual_time_of_arrival
                next_heuristic_time = self.heura(
                    destination_geopoint,
                    next_stop_node.stop.get_location(),
                    total_time)
                # Put it all together
                if next_stop_id not in self._min_arrival_time or next_actual_time < self._min_arrival_time[
                    next_stop_id]:
                    self._min_arrival_time[next_stop_id] = next_actual_time
                    self._min_path_taken[next_stop_id] = GoOnFoot(
                        current_node,
                        next_stop_node,
                        actual_time_of_arrival - MINIMUM_VARIANT_SWITCHING_TIME,
                        next_actual_time
                    )
                    queue.put(next_heuristic_time, next_actual_time, WALKED_LINE_VARIANT, next_stop_node)
                elif next_stop_node == destination_node:
                    total_times_destination_reached += 1

        # Post mortem, debug info
        logging.info("-" * 10)
        logging.info("A* search ended:")
        if not iteration_limit > total_iterations:
            logging.info(f"> Reached iteration limit: {iteration_limit}")
        elif not n_times_dest_reached < DOWNLOAD_PATH_FINDS + FINE_TUNE_PATH_FINDS:
            logging.info("> Reached path finding limit")
        elif queue.qsize() == 0:
            logging.info("> Queue empty!")
        else:
            logging.error("> Unknown reason")
        logging.info(f"Total times destination reached but not entered: {total_times_destination_reached}")
        logging.info(f"Total iterations per reach: {iterations_per_reach}")
        logging.info(f"Remaining queue elements: {queue.qsize()}")
        logging.info(f"Total chunks downloaded: {len(self._chunks)}")

    def calculate_whole_route(self, starting_time: Seconds_t, start_location: Union[Geopoint_t, int],
                              destination_location: Union[Geopoint_t, int]) -> list[NavStep]:
        """
        Calculates the path between start and end location.
        :param destination_location: geopoint or stop_id
        :param start_location: geopoint or stop_id
        :param starting_time: when does the journey start?
        :return: list on navsteps between start and end
        """

        modified_neighbours: list[tuple[float, int]] = []
        start_node = None
        destination_node = None

        if start_location == destination_location:
            raise Exception("Start and destination cant be in the same location!")

        if isinstance(start_location, tuple):
            # lat lng location as destination, create a fake node
            closest_stops = self._nav_data_model.get_n_closest_stops(MINIMUM_STOPS_IN_RANGE, start_location)
            start_node = FakeNetworkNode(
                FAKE_START_ID,
                "Punkt startowy!",
                start_location,
                closest_stops)
            self._graph.add_node(start_node)
        elif isinstance(start_location, int):
            # stop_id as start
            start_node = self._graph.get_nav_node(start_location)

        if isinstance(destination_location, tuple):
            # lat lng location as destination, create a fake node
            closest_stops = self._nav_data_model.get_n_closest_stops(MINIMUM_STOPS_IN_RANGE, destination_location)
            destination_node = FakeNetworkNode(
                FAKE_DESTINATION_ID,
                "Twój cel!",
                destination_location,
                closest_stops)
            self._graph.add_node(destination_node)

            # Connect the fake destination node to the graph
            modified_neighbours = closest_stops
            for distance, stop_id in closest_stops:
                self._graph.get_nav_node(stop_id).neighbours.append((distance, FAKE_DESTINATION_ID))
        elif isinstance(destination_location, int):
            # stop_id as destination
            destination_node = self._graph.get_nav_node(destination_location)

        logging.info(f"Calculating path between:")
        logging.info(f"{start_location} -> {str(start_node)}")
        logging.info(f"{destination_location} -> {str(destination_node)}")

        self._init_A_star(starting_time, start_node, destination_node)

        path = []
        current_node = destination_node
        reached_dead_end = False
        while not reached_dead_end:
            if current_node.stop.stop_id not in self._min_path_taken or current_node == start_node:
                reached_dead_end = True
                break

            current_nav_step = self._min_path_taken[current_node.stop.stop_id]
            if current_nav_step.destination_node is None:
                reached_dead_end = True
                break
            else:
                path.append(current_nav_step)
                current_node = current_nav_step.start_node

        # Undo graph changes
        if self._graph.stop_id_present(FAKE_START_ID):
            self._graph.remove_node(FAKE_START_ID)
        if self._graph.stop_id_present(FAKE_DESTINATION_ID):
            self._graph.remove_node(FAKE_DESTINATION_ID)
            for distance, stop_id in modified_neighbours:
                self._graph.get_nav_node(stop_id).neighbours.remove((distance, FAKE_DESTINATION_ID))

        return list(reversed(path))
