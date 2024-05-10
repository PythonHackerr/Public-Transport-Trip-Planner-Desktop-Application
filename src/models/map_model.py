import folium
import io
import sys
import json
from branca.element import Element
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage
from src.core.constants import DEFAULT_LOC_WARSAW
from src.models.stop_model import Stop
from src.lib.navigation_steps import GoOnFoot, TakeTransit
from src.controllers.pick_location_widget import PickLocationOnMap
from pathlib import Path
import logging
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QLabel, QPushButton
from functools import partial

PICKED_LOCATION = (0,0)

START_LOCATION = (0,0)
END_LOCATION = (0,0)


def get_widget_location(loc):
    global PICKED_LOCATION
    PICKED_LOCATION = loc


class CustomDialog(QDialog):
    def __init__(self, map, title_txt, nav_layout=None):
        super().__init__()
        self.location_chosen = None
        self.setWindowTitle(title_txt)
        self.nav = PickLocationOnMap(map)
        lavout = QVBoxLayout()
        lavout.addWidget(self.nav)
        button = QPushButton("Uzyskaj lokalizację")
        button.clicked.connect(self.nav.init_location_query)
        self.nav.location_ready.connect(get_widget_location)
        lavout.addWidget(button)
        self.setLayout(lavout)
        self.nav.setHtml(self.nav._map.get_root().render())
        self.nav.location_ready.connect(self.close)


class FoliumDisplay():
    def __init__(self, ui, nav_layout, pick_location=True):
        self._ui = ui
        self.map = None
        self.nav = None
        self._nav_layout = None
        
        self.map = folium.Map(location=DEFAULT_LOC_WARSAW, zoom_start=12)
        self.add_easter_egg()
        if (pick_location):
            self._nav_layout = nav_layout

            self._ui.webMap.setHtml(self.map.get_root().render())
            self._ui.pick_start_stop.clicked.connect(partial(self.pick_start_stop_button_clicked, self.map, self._ui))
            self._ui.pick_end_stop.clicked.connect(partial(self.pick_end_stop_button_clicked, self.map, self._ui))
            self._ui.show_route.clicked.connect(self.show_picked_route)
        else:
            self._ui.webMap.setHtml(self.map.get_root().render())
        
    def show_picked_route(self):
        global START_LOCATION, END_LOCATION, PICKED_LOCATION
        self._nav_layout._on_search(None)
        START_LOCATION = (0,0)
        END_LOCATION = (0,0)
        PICKED_LOCATION = (0,0)

    def pick_start_stop_button_clicked(self, map, ui):
        global START_LOCATION
        dlg = CustomDialog(map, "Uzyskaj lokalizację początkową")
        dlg.exec_()
        START_LOCATION = PICKED_LOCATION
        ui.searchBar1.setText(str(START_LOCATION))

    def pick_end_stop_button_clicked(self, map, ui):
        global END_LOCATION
        dlg = CustomDialog(map, "Uzyskaj lokalizację' końcową", self._nav_layout)
        dlg.exec_()
        END_LOCATION = PICKED_LOCATION
        ui.searchBar2.setText(str(END_LOCATION))


    def create_map(self, map_focus=DEFAULT_LOC_WARSAW, zoom=12):
        self.map = folium.Map(location=map_focus, zoom_start=zoom)
        self.add_easter_egg()
        
        if (self.nav == None):
            self._ui.webMap.setHtml(self.map.get_root().render())
        else:
            self.nav = PickLocationOnMap(self.map)
            self._ui.GetLocation.clicked.connect(self.nav.init_location_query)
            self.nav.location_ready.connect(get_widget_location)
            self._ui.webMap.setHtml(self.nav._map.get_root().render())

    


    def show_stop(self, stop: Stop = None, color="red"):
        if (self.map is None):
            self.create_map(stop.get_location())
        self.put_marker_on_stop(stop, color)
        if (self.nav == None):
            self._ui.webMap.setHtml(self.map.get_root().render())
        else:
            self.nav = PickLocationOnMap(self.map)
            self._ui.GetLocation.clicked.connect(self.nav.init_location_query)
            self.nav.location_ready.connect(get_widget_location)
            self._ui.webMap.setHtml(self.nav._map.get_root().render())

    def show_location(self, location, color="red"):
        if (self.map is None):
            self.create_map(location)
        self.put_marker_on_location(location, color)
        if (self.nav == None):
            self._ui.webMap.setHtml(self.map.get_root().render())
        else:
            self.nav = PickLocationOnMap(self.map)
            self._ui.GetLocation.clicked.connect(self.nav.init_location_query)
            self.nav.location_ready.connect(get_widget_location)
            self._ui.webMap.setHtml(self.nav._map.get_root().render())


    def show_line_path(self, points, color="red", dash_array='1'):
        if (self.map is None):
            self.create_map()

        self.connect_points(points, color, dash_array)
        if (self.nav == None):
            self._ui.webMap.setHtml(self.map.get_root().render())
        else:
            self.nav = PickLocationOnMap(self.map)
            self._ui.GetLocation.clicked.connect(self.nav.init_location_query)
            self.nav.location_ready.connect(get_widget_location)
            self._ui.webMap.setHtml(self.nav._map.get_root().render())

    def put_marker_on_stop(self, stop, color='red'):
        if not stop.has_location():
            return
        loc = stop.latitude, stop.longitude
        folium.Marker(loc, None, tooltip=str(stop), parse_html=True, icon=folium.Icon(color=color, icon='')).add_to(self.map)  # icon = pushpin (if favorite)

    def put_marker_on_location(self, location, color='red'):
        loc = location[0], location[1]
        folium.Marker(loc, None, tooltip=str("Wybrana lokalizacja"), parse_html=True, icon=folium.Icon(color=color, icon='')).add_to(self.map)  # icon = pushpin (if favorite)

    def show_nav_step(self, nav_step, color='red'):
        start_stop = nav_step.start_node.stop
        end_stop = nav_step.destination_node.stop
        for stop in start_stop, end_stop:
            self.show_stop(stop, color)

    def show_stops(self, stops, color='red', start_color="red", end_color="red", highlighted_stop_ids=[], highlighted_stop_color="black"):
        for stop in stops:
            if (stop.stop_id in highlighted_stop_ids):
                self.show_stop(stop, highlighted_stop_color)
            elif (stops.index(stop) == 0):
                self.show_stop(stop, start_color)
            elif (stops.index(stop) == len(stops)-1):
                self.show_stop(stop, end_color)
            else:
                self.show_stop(stop, color)

    def connect_stops(self, stops, stops_color='red', start_stop_color='red', end_stop_color='red', line_color='red'):
        points = [s.get_location() for s in stops]
        self.connect_points(points, line_color)

        for stop in stops:
            if stops.index(stop) == 0:
                self.show_stop(stop, start_stop_color)
            elif stops.index(stop) == len(stops)-1:
                self.show_stop(stop, end_stop_color)
            else:
                self.show_stop(stop, stops_color)

        
    def connect_points(self, points, color="red", dash_array='1'):
        folium.PolyLine(points, color=color, weight=3, opacity=1, dash_array=dash_array).add_to(self.map)


    def calculate_average_focus(self, points):
        # focus on the selected one or just the average
        lat_sum, lon_sum = 0, 0
        n_points_with_loc = 0
        for point in points:
            n_points_with_loc += 1
            lat_sum += point[0]
            lon_sum += point[1]
        if n_points_with_loc > 0:
            lat_sum /= n_points_with_loc
            lon_sum /= n_points_with_loc
            map_focus = (lat_sum, lon_sum)
        else:
            map_focus = DEFAULT_LOC_WARSAW
        return map_focus


    def add_easter_egg(self):
        img_file = str(Path().absolute())+"/Assets/UA.png"
        folium.raster_layers.ImageOverlay(
            image=img_file,
            name="Legend",
            #bottom, left, top, right
            bounds=[[50.2, 30.2], [50.6, 30.8]],
            opacity=1,
            interactive=False,
            cross_origin=False,
            zindex=1
        ).add_to(self.map)
        folium.LayerControl().add_to(self.map)





if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = FoliumDisplay()
    w.show()
    sys.exit(app.exec_())
