from src.models.line_model import LineModel
from src.models.nav_data_model import NavDataModel
from src.lib.a_star_navigation import AStarNav
from src.models.stop_model import StopModel


def test_chunking():
    chunk = NavDataModel.get_chunk_from_location_and_time((52, 20.5), 15 * 60 * 60)

    lat_chunk = chunk >> 10
    lng_chunk = (chunk >> 5) & 0b11111

    assert lat_chunk == 4
    assert lng_chunk == 1


def test_simple_stop_stop():
    stop_model = StopModel()
    stop_model.get_all_stops()
    line_model = LineModel()
    model = NavDataModel(stop_model, line_model)
    nav = AStarNav(model)

    time = 15 * 60 * 60 + 20 * 60  # 15:20:00
    # STOP: Marszałkowska 06 from Metro Świętokrzyska (701406)
    start = 701406

    # STOP: pl.Bankowy 08 from pl.Bankowy (701608)
    end = 701608

    path = nav.calculate_whole_route(time, start, end)
    assert len(path) == 1

def test_simple_loc_loc():
    stop_model = StopModel()
    stop_model.get_all_stops()
    line_model = LineModel()
    model = NavDataModel(stop_model, line_model)
    nav = AStarNav(model)

    time = 15 * 60 * 60 + 20 * 60  # 15:20:00
    # STOP: Marszałkowska 06 from Metro Świętokrzyska (701406)
    start = (52.235106638456045, 21.008875045093827)

    # STOP: pl.Bankowy 08 from pl.Bankowy (701608)
    end = (52.243435656851894, 21.003204483997035)

    path = nav.calculate_whole_route(time, start, end)
    assert len(path) == 3

def test_line_switch_loc_loc():
    stop_model = StopModel()
    stop_model.get_all_stops()
    line_model = LineModel()
    model = NavDataModel(stop_model, line_model)
    nav = AStarNav(model)

    time = 15 * 60 * 60 + 20 * 60  # 15:20:00
    # https://goo.gl/maps/jqYqzvbbzeL4T6cr5
    start = (52.21559260459384, 20.860595574905474)

    # https://goo.gl/maps/qjDVuvtARCwWcYFs8
    end = (52.27577771225344, 20.865421960582022)

    path = nav.calculate_whole_route(time, start, end)
    assert (path[-1].time_end - path[0].time_start)/60 < 100