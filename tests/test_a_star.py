from src.lib.geodesic import EARTH_RADIUS, ground_distance
from src.lib.a_star_navigation import AStarNav
from src.lib.navigation_graph import TransitNetworkNode, FakeStop
from src.lib.navigation_steps import GoOnFoot
import src.lib.a_star_navigation
from src.models.nav_data_structures import VariantStops, SingleCourse
import math
from pytest import approx
from src.models.stop_model import Stop


def test_ground_distance():
    p1 = (0, 0)
    p2 = (90, 0)
    assert ground_distance(p1, p2) == approx(EARTH_RADIUS * math.pi / 2)

    p1 = (54.51907482244072, 18.548508112507978)
    p2 = (54.49382215753887, 18.43647339400119)
    assert ground_distance(p1, p2) == approx(7.76e+3, rel=0.002)

    p1 = (10, 10)
    p2 = (10, 10)
    assert ground_distance(p1, p2) == 0

    p1 = (52.2, 20.9)
    p2 = (52.2, 21)

    p3 = (52.3, 20.9)
    p4 = (52.3, 21)
    assert ground_distance(p1, p2) == approx(ground_distance(p3, p4), abs=25)

    # in warsaw:
    # 1 deg lng approx 68 km
    # 1 deg lat approx 111 km


def test_A_star_graph_building():
    # G1
    nav = AStarNav()

    st1 = Stop(1, "xx", "y1y", 51.03, 20.01, "z1z", "abc", "xxx", "yyy")
    st2 = Stop(2, "xx", "y2y", 51.02, 20.00, "z2z", "abc", "xxx", "yyy")
    st3 = Stop(3, "xx", "y3y", 51.01, 20.00, "z3z", "abc", "xxx", "yyy")
    st4 = Stop(4, "xx", "y4y", 51.01, 20.02, "z4z", "abc", "xxx", "yyy")
    st5 = Stop(5, "xx", "y5y", 51.02, 20.02, "z5z", "abc", "xxx", "yyy")
    st6 = Stop(6, "xx", "y6y", 51.00, 20.01, "z6z", "abc", "xxx", "yyy")

    L1_variant = VariantStops(
        "L1",
        [1, 2, 3, 6, 4]
    )
    L1_courses = [
        SingleCourse("L1-1", L1_variant, {1: 50, 2: 250, 3: 550, 6: 750, 4: 950}),
        SingleCourse("L1-2", L1_variant, {1: 300, 2: 500, 3: 800, 6: 1000, 4: 1200}),
        SingleCourse("L1-3", L1_variant, {1: 600, 2: 800, 3: 1100, 6: 1300, 4: 1500})
    ]
    L2_variant = VariantStops(
        "L2",
        [1, 5, 4, 6]
    )
    L2_courses = [
        SingleCourse("L2-1", L2_variant, {1: 100, 5: 400, 4: 1400, 6: 1700}),
        SingleCourse("L2-2", L2_variant, {1: 300, 5: 600, 4: 1600, 6: 1900}),
        SingleCourse("L2-3", L2_variant, {1: 500, 5: 800, 4: 18000, 6: 2100})
    ]
    L3_variant = VariantStops(
        "L3",
        [3, 4]
    )
    L3_courses = [
        SingleCourse("L3-1", L3_variant, {3: 200, 4: 400}),
        SingleCourse("L3-1", L3_variant, {3: 600, 4: 800})
    ]

    nav.graph.add_node(TransitNetworkNode(
        st1,
        {
            "L1": L1_courses,
            "L2": L2_courses
        },
        []
    ))
    nav.graph.add_node(TransitNetworkNode(
        st2,
        {
            "L1": L1_courses,
        },
        []
    ))
    nav.graph.add_node(TransitNetworkNode(
        st3,
        {
            "L1": L1_courses,
            "L3": L3_courses
        },
        []
    ))
    nav.graph.add_node(TransitNetworkNode(
        st4,
        {
            "L1": L1_courses,
            "L2": L2_courses,
            "L3": L3_courses
        },
        []
    ))
    nav.graph.add_node(TransitNetworkNode(
        st5,
        {
            "L2": L2_courses
        },
        []
    ))
    nav.graph.add_node(TransitNetworkNode(
        st6,
        {
            "L1": L1_courses
        },
        []
    ))

    assert nav.graph.get_nav_node(4).stop.stop_id == 4
    assert len(nav.graph.get_nav_node(4).line_variant_courses) == 3
    assert nav.graph.get_nav_node(4).line_variant_courses["L1"][0].course_id == "L1-1"
    assert nav.graph.get_nav_node(4).line_variant_courses["L1"][0].times_of_arrival_per_stop_id[4] == 950
    assert nav.graph.get_nav_node(4).line_variant_courses["L1"] == L1_courses

    assert nav.graph.get_nav_node(1).find_soonest_course_of_variant_on_this_stop(0, "L2") == L2_courses[0]
    assert nav.graph.get_nav_node(1).find_soonest_course_of_variant_on_this_stop(400, "L2") == L2_courses[2]


def test_in_stop_line_switching_and_indirectness():
    # G1
    nav = AStarNav()

    st1 = Stop(1, "xx", "y1y", 51.03, 20.01, "z1z", "abc", "xxx", "yyy")
    st2 = Stop(2, "xx", "y2y", 51.02, 20.00, "z2z", "abc", "xxx", "yyy")
    st3 = Stop(3, "xx", "y3y", 51.01, 20.00, "z3z", "abc", "xxx", "yyy")
    st4 = Stop(4, "xx", "y4y", 51.01, 20.02, "z4z", "abc", "xxx", "yyy")
    st5 = Stop(5, "xx", "y5y", 51.02, 20.02, "z5z", "abc", "xxx", "yyy")
    st6 = Stop(6, "xx", "y6y", 51.00, 20.01, "z6z", "abc", "xxx", "yyy")

    L1_variant = VariantStops(
        "L1",
        [1, 2, 3, 6, 4]
    )
    L1_courses = [
        SingleCourse("L1-1", L1_variant, {1: 50, 2: 250, 3: 550, 6: 750, 4: 950}),
        SingleCourse("L1-2", L1_variant, {1: 300, 2: 500, 3: 800, 6: 1000, 4: 1200}),
        SingleCourse("L1-3", L1_variant, {1: 600, 2: 800, 3: 1100, 6: 1300, 4: 1500})
    ]
    L2_variant = VariantStops(
        "L2",
        [1, 5, 4, 6]
    )
    L2_courses = [
        SingleCourse("L2-1", L2_variant, {1: 100, 5: 400, 4: 1400, 6: 1700}),
        SingleCourse("L2-2", L2_variant, {1: 300, 5: 600, 4: 1600, 6: 1900}),
        SingleCourse("L2-3", L2_variant, {1: 500, 5: 800, 4: 18000, 6: 2100})
    ]
    L3_variant = VariantStops(
        "L3",
        [3, 4]
    )
    L3_courses = [
        SingleCourse("L3-1", L3_variant, {3: 200, 4: 400}),
        SingleCourse("L3-1", L3_variant, {3: 600, 4: 800})
    ]

    nav.graph.add_node(TransitNetworkNode(
        st1,
        {
            "L1": L1_courses,
            "L2": L2_courses
        },
        []
    ))
    nav.graph.add_node(TransitNetworkNode(
        st2,
        {
            "L1": L1_courses,
        },
        []
    ))
    nav.graph.add_node(TransitNetworkNode(
        st3,
        {
            "L1": L1_courses,
            "L3": L3_courses
        },
        []
    ))
    nav.graph.add_node(TransitNetworkNode(
        st4,
        {
            "L1": L1_courses,
            "L2": L2_courses,
            "L3": L3_courses
        },
        []
    ))
    nav.graph.add_node(TransitNetworkNode(
        st5,
        {
            "L2": L2_courses
        },
        []
    ))
    nav.graph.add_node(TransitNetworkNode(
        st6,
        {
            "L1": L1_courses
        },
        []
    ))

    route = nav.calculate_whole_route(0, 1, 4)
    assert len(route) == 2
    assert route[0].time_start == 50
    assert route[0].time_end == 550
    assert route[1].time_start == 600
    assert route[1].time_end == 800
    assert nav._min_arrival_time[4] == 800


def test_walking_to_neighbour():
    # G2
    nav = AStarNav()

    st1 = Stop(1, "xx", "y1y", 51.03, 20.02, "z1z", "abc", "xxx", "yyy")
    st2 = Stop(2, "xx", "y2y", 51.02, 20.01, "z2z", "abc", "xxx", "yyy")
    st3 = Stop(3, "xx", "y3y", 51.01, 20.00, "z3z", "abc", "xxx", "yyy")
    st4 = Stop(4, "xx", "y4y", 51.005, 20.00, "z4z", "abc", "xxx", "yyy")
    st5 = Stop(5, "xx", "y5y", 51.005, 20.01, "z5z", "abc", "xxx", "yyy")
    st6 = Stop(6, "xx", "y6y", 51.005, 20.02, "z6z", "abc", "xxx", "yyy")

    L1_variant = VariantStops(
        "L1",
        [1, 2, 3]
    )
    L1_courses = [
        SingleCourse("L1-1", L1_variant, {1: 100, 2: 300, 3: 500})
    ]
    L2_variant = VariantStops(
        "L2",
        [4, 5, 6]
    )
    L2_courses = [
        SingleCourse("L2-1", L2_variant, {4: 800, 5: 1000, 6: 1200})
    ]

    nav.graph.add_node(TransitNetworkNode(
        st1,
        {
            "L1": L1_courses
        },
        []
    ))
    nav.graph.add_node(TransitNetworkNode(
        st2,
        {
            "L1": L1_courses,
        },
        []
    ))
    nav.graph.add_node(TransitNetworkNode(
        st3,
        {
            "L1": L1_courses
        },
        [(200, 4)]
    ))
    nav.graph.add_node(TransitNetworkNode(
        st4,
        {
            "L2": L2_courses,
        },
        [(200, 3)]
    ))
    nav.graph.add_node(TransitNetworkNode(
        st5,
        {
            "L2": L2_courses
        },
        []
    ))
    nav.graph.add_node(TransitNetworkNode(
        st6,
        {
            "L2": L2_courses
        },
        []
    ))

    route = nav.calculate_whole_route(0, 1, 6)
    assert isinstance(nav._min_path_taken[4], GoOnFoot)
    assert nav._min_arrival_time[6] == 1200


def test_heuristics_impact_on_indirect_routes():
    # G3
    nav = AStarNav()

    st1 = Stop(1, "xx", "y1y", 51.03, 20.00, "z1z", "abc", "xxx", "yyy")
    st2 = Stop(2, "xx", "y2y", 51.02, 20.00, "z2z", "abc", "xxx", "yyy")
    st3 = Stop(3, "xx", "y3y", 51.02, 20.01, "z3z", "abc", "xxx", "yyy")
    st4 = Stop(4, "xx", "y4y", 51.01, 20.00, "z4z", "abc", "xxx", "yyy")
    st5 = Stop(5, "xx", "y5y", 51.01, 20.01, "z5z", "abc", "xxx", "yyy")

    L1_variant = VariantStops(
        "L1",
        [2, 4]
    )
    L1_courses = [
        SingleCourse("L1-1", L1_variant, {2: 300, 4: 1800})
    ]
    L2_variant = VariantStops(
        "L2",
        [3, 5]
    )
    L2_courses = [
        SingleCourse("L2-1", L2_variant, {3: 1000, 5: 1200})
    ]
    L3_variant = VariantStops(
        "L2",
        [1, 2, 3]
    )
    L3_courses = [
        SingleCourse("L3-1", L3_variant, {1: 50, 2: 250, 3: 850})
    ]
    L4_variant = VariantStops(
        "L2",
        [5, 4]
    )
    L4_courses = [
        SingleCourse("L4-1", L4_variant, {5: 1300, 4: 1500})
    ]

    nav.graph.add_node(TransitNetworkNode(
        st1,
        {
            "L3": L3_courses,
        },
        []
    ))
    nav.graph.add_node(TransitNetworkNode(
        st2,
        {
            "L3": L3_courses,
            "L1": L1_courses,
        },
        []
    ))
    nav.graph.add_node(TransitNetworkNode(
        st3,
        {
            "L3": L3_courses,
            "L2": L2_courses,
        },
        []
    ))
    nav.graph.add_node(TransitNetworkNode(
        st4,
        {
            "L1": L1_courses,
            "L4": L4_courses,
        },
        []
    ))
    nav.graph.add_node(TransitNetworkNode(
        st5,
        {
            "L2": L2_courses,
            "L4": L4_courses,
        },
        []
    ))

    route1 = nav.calculate_whole_route(0, 1, 4)
    assert len(route1) == 3
    assert route1[-1].time_end == 1500

    src.lib.a_star_navigation.HEURISTIC_STRAIGHT_LINE_SPEED = 0.001

    route2 = nav.calculate_whole_route(0, 1, 4)
    assert len(route2) == 3
    assert route2[-1].time_end == 1500


def test_nav_node_course_sorting():
    vs = VariantStops("xyz", [1, 2, 5, 7])
    sc1 = SingleCourse("abc", vs, {1: 15, 2: 65, 5: 69, 7: 98})
    sc2 = SingleCourse("abc", vs, {1: 17, 2: 68, 5: 77, 7: 102})
    stop = FakeStop(69, "space x :)", (0, 0))
    node = TransitNetworkNode(stop, {}, [])
    node.add_course(sc2)
    node.add_course(sc1)
    assert not node._ordered
    node.order_courses()
    assert node._ordered
    assert node.line_variant_courses["xyz"][0] == sc1
