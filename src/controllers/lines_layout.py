import sys
import folium
import logging
from src.models.user_config_model import UserConfigModel
from src.models.line_model import Line, Route, LineModel
from src.models.stop_model import StopComplex, Stop, StopModel
from src.core.controller import Controller
from src.views.ui_lines_layout import Ui_LinesLayoutUI
from PySide6.QtWidgets import QWidget, QCompleter, QApplication, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QScrollArea, QTabWidget, QGroupBox, QGridLayout
from PySide6.QtCore import QStringListModel, Qt, QThread
from PySide6.QtGui import QFont
import PySide6.QtCore as QtCore
import random
import functools
import datetime
from src.models.map_model import FoliumDisplay
from PySide6.QtGui import QIcon
from pathlib import Path

class LinesLayoutDownload(QThread):
    def __init__(self, line_model: LineModel):
        super().__init__()
        self._line_model = line_model
        self.lines = None

    def run(self) -> None:
        self.lines = self._line_model._get_all_lines()


class LinesLayout(Controller, QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._ui = Ui_LinesLayoutUI()
        self._ui.setupUi(self)
        self._ui.webMap.setHidden(True)
        # Models
        self._user_config = UserConfigModel.get_instance()
        self._line_model = LineModel()

        self._download_thread = LinesLayoutDownload(self._line_model)
        self._download_thread.finished.connect(self._on_init_data_download_complete)
        self._download_thread.start()


    def _on_init_data_download_complete(self):
        logging.info("_on_init_data_download_complete")
        self._grid_layout = QGridLayout()
        self._lines = self._download_thread.lines
        
        rows = 14
        for column in range((len(self._lines) // rows) + 1):
            for row in range(rows):
                if (column * rows + row >= len(self._lines)):
                    break
                self.button = QPushButton(f"{self._lines[column * rows + row].line_id}", clicked = functools.partial(self.init_next_layout, self._lines[column * rows + row]))#clicked = functools.partial(self.main_window.change_lines_widget, next_layout)
                
                line_type_id = self._lines[column * rows + row].line_type_id
                line_type = self._line_model._get_line_type_by_type_id(line_type_id).name
                if (line_type == "LINIA TRAMWAJOWA" or line_type == "LINIA TRAMWAJOWA UZUPEŁNIAJĄCA"): # tram
                    self.button.setStyleSheet('QPushButton {background-color: #b3cf99; color: black; font: bold 14px;}')
                elif (line_type == "LINIA KOLEI MIEJSKIEJ"): # train
                    self.button.setStyleSheet('QPushButton {background-color: #d21f3c; color: black; font: bold 14px;}')
                else: # bus
                    self.button.setStyleSheet('QPushButton {background-color: #45b6fe; color: black; font: bold 14px;}')

                self._grid_layout.addWidget(self.button, column, row, 1, 1)

        self._grid_layout.setSpacing(1)
    
        self.setLayout(self._grid_layout)
        self.setEnabled(True)


    def init_next_layout(self, line):
        next_layout = RoutesLayout(self.main_window, line);
        self.main_window.change_lines_widget(next_layout)


class RoutesLayoutDownload(QThread):
    def __init__(self, line_model: LineModel, line):
        super().__init__()
        self._line_model = line_model
        self._line = line
        self.line_routes = None
        self.route_types = None

    def run(self) -> None:
        self.line_routes, self.route_types = self._line_model._get_line_routes(self._line.line_id)


class RoutesLayout(Controller, QWidget):

    def __init__(self, main_window, line, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._ui = Ui_LinesLayoutUI()
        self._ui.setupUi(self)
        self._line = line

        # Models
        # TODO: threaded data download!!!
        self._user_config = UserConfigModel.get_instance()
        self._line_model = LineModel()
        self._map_model = FoliumDisplay(self._ui, None, False)
        self._download_thread = RoutesLayoutDownload(self._line_model, line)
        self._download_thread.finished.connect(self._on_init_data_download_complete)
        self._download_thread.start()


    def _on_init_data_download_complete(self):
        self._line_routes = self._download_thread.line_routes
        self._route_types = self._download_thread.route_types
        self._ui.titleLabel.setText(f"Wybierz wariant trasy dla linii {self._line.line_id}")
        
        for route in self._line_routes:
            self._horizontal_layout = QHBoxLayout()
            # self._horizontal_layout.addWidget(QLabel(f"{route.variant_id}", self), 1)
            self._horizontal_layout.addWidget(QLabel(f"{route.variant_name}", self), 1)
            bt = QPushButton(f"{route.destination[1].name} {route.destination[0].name}", clicked = functools.partial(self.init_next_layout, route))
            self._horizontal_layout.addWidget(bt, 4)
            bt = QPushButton(f"Pokaż na mapie", clicked = functools.partial(self.show_line_route, route.variant_id))
            icon = QIcon(str(Path().absolute())+"/Assets/show_on_map_icon.png".format("file_important"))
            bt.setIcon(icon)
            self._horizontal_layout.addWidget(bt, 2)
            self._ui.verticalLayout.addLayout(self._horizontal_layout, 1)


    def show_line_route(self, variant_id):
        stops = self._line_model._get_stops_of_route(variant_id)
        self._map_model.create_map(self._map_model.calculate_average_focus([stop.get_location() for stop in stops]))
        self._map_model.connect_stops(stops, "orange", "red", "purple", "green")


    def init_next_layout(self, route):
        next_layout = StopsLayout(self.main_window)
        self.main_window.change_lines_widget(next_layout)
        next_layout._create_stops_table(route)



class Street:
    def __init__(self, name: str):
        self._name = name



class StopsLayout(Controller, QWidget):

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        
        self._ui = Ui_LinesLayoutUI()
        self._ui.setupUi(self)
        # Models
        # TODO: threaded data download!!!
        self._user_config = UserConfigModel.get_instance()
        self._stop_model = StopModel()
        #self._create_routes_table()

    def _create_stops_table(self, route):
        self._route = route
        self.scroll = QScrollArea() # Scroll Area which contains the widgets, set as the centralWidget
        self.widget = QWidget() # Widget that contains the collection of Vertical Box
        self._vertical_layout = QVBoxLayout() # The Vertical Box that contains the Horizontal Boxes of labels and buttons

        counter = 0
        for stop in self._route._stops:
            counter += 1
            self._horizontal_layout = QHBoxLayout()
            
            self._horizontal_layout.addWidget(QLabel(f"№{counter}", self), 1)
            self._horizontal_layout.addWidget(QPushButton(f"{self._stop_model.get_complex_by_id(stop.stop_complex_id).name} {stop.stop_number}",
               clicked = functools.partial(self.init_next_layout, stop, self._route)), 5)
            self._horizontal_layout.addWidget(QLabel(f"{stop.street}"), 2)
            self._vertical_layout.addLayout(self._horizontal_layout)

        self.widget.setLayout(self._vertical_layout)
        #Scroll Area Properties
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.widget)

        layoutt = QVBoxLayout(self)
        layoutt.addWidget(self.scroll)

        self.setLayout(self._vertical_layout)


    def init_next_layout(self,route,  stop ):
        next_layout = TimeTableLayout(self.main_window, route, stop)
        self.main_window.change_lines_widget(next_layout)



class TimeTableLayoutDownload(QThread):
    def __init__(self, stop_model: StopModel, route, stop):
        super().__init__()
        self._stop_model = stop_model
        self.time_departures = None
        self._route = route
        self._stop = stop
        
    def run(self) -> None:
        self.time_departures = self._stop_model.get_time_departures_from_stop_of_route(self._route, self._stop.stop_id)


class TimeTableLayout(Controller, QWidget):

    def __init__(self, main_window, stop, route, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._stop = stop
        self._route = route
        
        self._ui = Ui_LinesLayoutUI()
        self._ui.setupUi(self)
        # Models
        self._user_config = UserConfigModel.get_instance()
        self._stop_model = StopModel()
        
        self._download_thread = TimeTableLayoutDownload(self._stop_model, route, stop)
        self._download_thread.finished.connect(self._on_init_data_download_complete)
        self._download_thread.start()


    def to_matrix(self, l, n):
        return [l[i:i+n] for i in range(0, len(l), n)]


    def _on_init_data_download_complete(self):
        self.scroll = QScrollArea() # Scroll Area which contains the widgets, set as the centralWidget
        self.widget = QWidget() # Widget that contains the collection of Vertical Box
        self._grid_layout = QGridLayout() # The Grid Layout that contains the Boxes of labels

        time_departures = self._download_thread.time_departures
        time_departures_integers = sorted([int(t) for t in time_departures])
        time_departures = time_departures_integers
        time_departures = self.to_matrix(time_departures, 5)

        for i in range(len(time_departures)):
            for j in range(5):
                if (len(time_departures[i]) <= j):
                    break
                time_str = str(datetime.timedelta(minutes=int(time_departures[i][j]))).replace("1 day, ", "")
                self._grid_layout.addWidget(QLabel(f"{time_str}"), i, j)

        self.widget.setLayout(self._grid_layout)

        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.widget)

        qvBoxLayout = QVBoxLayout(self)
        qvBoxLayout.addWidget(self.scroll)

        self.setLayout(self._grid_layout)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LinesLayout(None)
    window.show()
    app.exec()