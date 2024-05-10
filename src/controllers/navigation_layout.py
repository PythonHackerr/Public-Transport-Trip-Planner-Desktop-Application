import sys
import folium
import logging
from src.controllers.stop_layout import FavouritesGroup
from src.models.user_config_model import UserConfigModel
from src.lib.a_star_navigation import AStarNav, NavStep, TransitNetworkNode, NavDataModel
from src.lib.navigation_steps import GoOnFoot, StartAtNode, TakeTransit
from src.models.stop_model import StopComplex, Stop, StopModel, STOP_COMPLEX_OBJECT_TYPE, STOP_OBJECT_TYPE
from src.models.line_model import LineModel, NavRoute
from src.core.controller import Controller
from src.views.ui_navigation_layout import Ui_WidgetNavigation
from PySide6.QtWidgets import QWidget, QCompleter, QApplication, QTreeWidgetItem, QMenu, QInputDialog, QMessageBox, QListWidgetItem
from PySide6.QtCore import QStringListModel, Qt, QThread, QTime, QSize
from datetime import date
from datetime import datetime, timedelta
from PySide6.QtGui import QAction, QIcon, QPixmap
import functools
from pathlib import Path
from src.models.map_model import FoliumDisplay
from time import strftime
from time import gmtime


class StopListItem(QListWidgetItem):
    def __init__(self, start_stop: Stop, end_stop: Stop, icon=None, additional_notes=[]):
        super().__init__()
        spacing = " " * 4
        additional_notes_txt = ""
        for note in additional_notes:
            additional_notes_txt += "\n" + spacing + note
        self.setText(spacing + str(start_stop).replace("Przystanek: ", "").replace("N/A N/A", "lokalizacja startowa") + " -> " + str(end_stop).replace("Przystanek: ", "").replace("N/A N/A", "lokalizacja końcowa") + additional_notes_txt)
        if (icon != None):
            self.setIcon(icon)
        self._start_stop = start_stop
        self._end_stop = end_stop


    def get_start_stop(self):
        return self._start_stop

    def get_end_stop(self):
        return self._end_stop



class TextListItem(QListWidgetItem):
    def __init__(self, txt):
        super().__init__()
        self.setText(txt)


class RouteTreeItem(QTreeWidgetItem):
    def __init__(self, name: str, group: FavouritesGroup, route: NavRoute):
        super().__init__(group)
        self._name = name
        self._route = route
        self._group = group

        self.setText(0, name)

    def get_route(self):
        return self._route

    def get_group(self):
        return self.parent().get_name()

    def get_name(self):
        return self._name



class NavigationLayoutDownload(QThread):
    def __init__(self, stop_model: StopModel, line_model: LineModel):
        super().__init__()
        self._stop_model = stop_model
        self._line_model = line_model
        self.stops = None
        self.variant_stops = None

    def run(self) -> None:
        self.stops = self._stop_model.get_all_stops()
        self._line_model.all_lines_routes = self._line_model._get_all_lines_routes()



class NavStepsDownload(QThread):
    def __init__(self, astar_model: AStarNav, selected_time, object_id_start, object_id_end):
        super().__init__()
        self._astar_model = astar_model
        self.nav_steps = None
        self._selected_time = selected_time
        self._object_id_start = object_id_start
        self._object_id_end = object_id_end

    def run(self) -> None:
        midnight_time = datetime.combine(date.min, datetime.min.time())
        self.nav_steps = self._astar_model.calculate_whole_route((self._selected_time - midnight_time).seconds, self._object_id_start, self._object_id_end)



class NavigationLayout(Controller, QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ui = Ui_WidgetNavigation()
        self._ui.setupUi(self)

        self.setDisabled(True)
        self.map_model = FoliumDisplay(self._ui, self)
        
        # Models
        self._stop_model = StopModel()
        self._line_model = LineModel()
        self._user_config = UserConfigModel.get_instance()
        self._nav_model = NavDataModel(self._stop_model, self._line_model)
        self._astar_model = AStarNav(self._nav_model)

        self._nav_steps_thread = None
        self._download_thread = NavigationLayoutDownload(self._stop_model, self._line_model)
        self._download_thread.finished.connect(self._on_init_data_download_complete)
        self._download_thread.start()

    def _on_init_data_download_complete(self):
        self._inter_stops = []
        self._nav_steps = []
        self._current_route = None

        self._current_stop: Stop = None
        self._stop_complex_names_qmodel = QStringListModel()
        stop_identifiers = [stop.readable_identifier for stop in self._download_thread.stops]

        self._stop_complex_names_qmodel.setStringList(stop_identifiers)

        self._search_bar1_completer = QCompleter()
        self._search_bar1_completer.setModel(self._stop_complex_names_qmodel)
        self._search_bar1_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._search_bar1_completer.setFilterMode(Qt.MatchFlag.MatchContains)

        self._search_bar2_completer = QCompleter()
        self._search_bar2_completer.setModel(self._stop_complex_names_qmodel)
        self._search_bar2_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._search_bar2_completer.setFilterMode(Qt.MatchFlag.MatchContains)

        self._ui.timeEdit.setTime(QTime.currentTime())

        self.now = datetime.now()
        self.midnight_time = datetime.combine(date.min, datetime.min.time())
        self.seconds_since_midnight = (self.now - self.now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()

        self.map_model.create_map()
        self._ui_finalize()
        self._set_up_triggers()
        self.setEnabled(True)

    def _ui_finalize(self):
        self._ui.searchBar1.setCompleter(self._search_bar1_completer)
        self._ui.searchBar2.setCompleter(self._search_bar2_completer)
        self._reload_favourites()
        self._reload_fav_button()

    def _set_up_triggers(self):
        self._ui.searchBar1.returnPressed.connect(lambda: self._on_search())
        self._ui.searchBar2.returnPressed.connect(lambda: self._on_search())
        self._ui.StopsQListWidget.itemDoubleClicked.connect(self._on_stop_focus)

        self._ui.btRemoveFav.clicked.connect(self._on_favourite_delete)
        self._ui.FavouritesQTreeWidget.itemDoubleClicked.connect(self._on_jump_to_favourite)
        # When favourites are updated...
        self._user_config.favourite_routes_updated.connect(self._reload_favourites)
        self._user_config.groups_routes_updated.connect(self._reload_fav_button)
        self._ui.btNewGroup.clicked.connect(self._on_new_group)

        # path = str(Path().absolute()).replace('\\', "/")+"/Assets/blank.png"
        pixmap = QPixmap((str(Path().absolute())+"/Assets/add_icon.png".format("file_important")))
        icon = QIcon(pixmap)
        self._ui.btNewGroup.setIcon(icon)
        self._ui.btNewGroup.setIconSize(QSize(20,22))
        # self._ui.btNewGroup.setStyleSheet(f"background-image : url();")
        pixmap = QPixmap((str(Path().absolute())+"/Assets/remove_icon.png".format("file_important")))
        icon = QIcon(pixmap)
        self._ui.btRemoveFav.setIcon(icon)
        self._ui.btRemoveFav.setIconSize(QSize(20,22))


    def show_message_box(self, title, txt):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(txt)
        button = msg.exec()
        if button == QMessageBox.StandardButton.Ok:
            pass


    def _on_stop_focus(self, selection: StopListItem):
        self._inter_stops = [ns.start_node.stop for ns in self._nav_steps]
        self._on_nav_steps_complete(STOP_OBJECT_TYPE, STOP_OBJECT_TYPE, [selection.get_start_stop().stop_id, selection.get_end_stop().stop_id], "black")

    def _on_new_group(self):
        ret = QInputDialog.getText(self, "Nowa grupa", "Nowa nazwa grupy")
        group, success = ret
        if success:
            try:
                self._user_config.add_new_routes_group(group)
                logging.info(f"Adding new favourite group: {group}")
                self._reload_favourites()
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))


    def get_arrival_time_from_now(self, time):
        t = datetime.strptime(strftime("%H:%M:%S", gmtime(time)), '%H:%M:%S').time()
        secs = (datetime.combine(date.min, t) - self.midnight_time) - timedelta(0, self.seconds_since_midnight)
        arrival_time = f"{str(timedelta(seconds=secs.seconds))}"
        return arrival_time

    def get_arrival_time(self, time):
        t = datetime.strptime(strftime("%H:%M:%S", gmtime(time)), '%H:%M:%S').time()
        arrival_time = datetime.combine(date.min, t) - self.midnight_time
        return arrival_time



    def show_stops_list(self):
        stops = [ns.start_node.stop for ns in self._nav_steps]
        if (len(self._nav_steps) > 0):
            stops.append(self._nav_steps[-1:][0].destination_node.stop)

        self._ui.StopsQListWidget.setSortingEnabled(False)
        self._ui.StopsQListWidget.clear()
        self._ui.StopsQListWidget.setSpacing(2)

        self._ui.StopsQListWidget.addItem(
            TextListItem(f"Typ  |  Informacja o przystanku")
        )
        icon = None
        last_line_taken = None
        for nav_step in self._nav_steps:
            start_time = self.get_arrival_time(nav_step.time_start)
            end_time = self.get_arrival_time(nav_step.time_end)
            if (isinstance(nav_step, GoOnFoot)):
                icon = QIcon(str(Path().absolute())+"/Assets/walk_icon.png".format("file_important"))
                self._ui.StopsQListWidget.addItem(StopListItem(nav_step.start_node.stop, nav_step.destination_node.stop, icon, [f"{start_time} - {end_time}"]))
                last_line_taken = None
            else:
                line_type = self._line_model._get_line_type_by_variant_id(nav_step.line_variant).name
                line_id = self._line_model._get_line_by_variant_id(nav_step.line_variant).name
                line_name = ""
                if (line_type == "LINIA TRAMWAJOWA" or line_type == "LINIA TRAMWAJOWA UZUPEŁNIAJĄCA"): # tram
                    icon = QIcon(str(Path().absolute())+"/Assets/tram_icon.png".format("file_important"))
                    line_name = "tramwajową"
                elif (line_type == "LINIA KOLEI MIEJSKIEJ"): # train
                    icon = QIcon(str(Path().absolute())+"/Assets/train_icon.png".format("file_important"))
                    line_name = "pociągową"
                else: # bus
                    icon = QIcon(str(Path().absolute())+"/Assets/bus_icon.png".format("file_important"))
                    line_name = "autobusową"

                start_time = self.get_arrival_time(nav_step.time_start)
                end_time = self.get_arrival_time(nav_step.time_end)
                if (last_line_taken != line_id):
                    self._ui.StopsQListWidget.addItem(StopListItem(nav_step.start_node.stop, nav_step.destination_node.stop, icon, [f"Teraz weź linię {line_name} {line_id}", f"{start_time} - {end_time}"]))
                else:
                    self._ui.StopsQListWidget.addItem(StopListItem(nav_step.start_node.stop, nav_step.destination_node.stop, icon, [f"Teraz weź linię {line_name} {line_id}", f"{start_time} - {end_time}"]))
                last_line_taken = line_id
            

        self._ui.StopsQListWidget.setSortingEnabled(True)


    def _on_jump_to_favourite(self, selection: QTreeWidgetItem):
        if isinstance(selection, RouteTreeItem):
            self._on_search(selection.get_route())

    def _on_favourite_delete(self):
        selection = self._ui.FavouritesQTreeWidget.selectedItems()

        groups = []
        removal_list = []
        for item in selection:
            if isinstance(item, FavouritesGroup):
                groups.append(item.get_name())
            elif isinstance(item, RouteTreeItem):
                removal_list.append((item.get_group(), item.get_route()))

        self._user_config.remove_routes_groups(groups, no_emit=True)
        self._user_config.remove_favourite_routes(removal_list)

    def _reload_favourites(self):
        self._ui.FavouritesQTreeWidget.setSortingEnabled(False)
        self._ui.FavouritesQTreeWidget.clear()
        for group in self._user_config.get_favourite_routes():
            group_item = FavouritesGroup(group, True)
            self._ui.FavouritesQTreeWidget.addTopLevelItem(group_item)
            for route in self._user_config.get_favourites_routes_by_group(group):
                stop_start = str(self._stop_model.get_stop_by_id(route.start_stop_id)).replace("Przystanek: ", "")
                stop_end = str(self._stop_model.get_stop_by_id(route.destination_stop_id)).replace("Przystanek: ", "")
                item_name = f"{stop_start} -> {stop_end}"
                item = RouteTreeItem(item_name, group_item, route)

        self._ui.FavouritesQTreeWidget.setSortingEnabled(True)


    def _reload_fav_button(self):
        self._fav_menu = QMenu()
        self._fav_menu_actions = []
        for group in self._user_config.get_routes_groups():
            action = QAction()
            action.setText(group)
            action.triggered.connect(functools.partial(self._add_current_route_to_favourites, group=group))
            self._fav_menu.addAction(action)
            self._fav_menu_actions.append(action)

        if len(self._fav_menu_actions) == 0:
            no_groups_prompt = QAction()
            no_groups_prompt.setText("Najpierw musisz stworzyć grupę!")
            no_groups_prompt.setDisabled(True)
            self._fav_menu.addAction(no_groups_prompt)
            self._fav_menu_actions.append(no_groups_prompt)
        self._ui.btFavourite.setMenu(self._fav_menu)
        icon = QIcon(str(Path().absolute())+"/Assets/save_icon.png".format("file_important"))
        self._ui.btFavourite.setIcon(icon)

        icon = QIcon(str(Path().absolute())+"/Assets/show_on_map_icon.png".format("file_important"))
        self._ui.pick_start_stop.setIcon(icon)
        icon = QIcon(str(Path().absolute())+"/Assets/show_on_map_icon.png".format("file_important"))
        self._ui.pick_end_stop.setIcon(icon)


    def _add_current_route_to_favourites(self, group):
        if self._current_route is None:
            try:
                object_type_start, object_id_start = self._stop_model.parse_readable_identifier(self._ui.searchBar1.text())
                object_type_end, object_id_end = self._stop_model.parse_readable_identifier(self._ui.searchBar2.text())
                if (object_id_start == -2 or object_id_start == -1):
                    object_id_start = self._nav_steps[0].destination_node.stop.stop_id
                if (object_id_end == -1 or object_id_end == -2):
                    object_id_end = self._nav_steps[len(self._nav_steps)-1].start_node.stop.stop_id
                if (object_id_start == object_id_end): 
                    self.show_message_box("Uwaga!", "Przystanki startowy i końcowy nie mogą być tym samym przystankiem!")
                    return
                self._current_route = NavRoute(object_id_start, object_id_end)
            except:
                self.show_message_box("Uwaga!", "Możesz zapisać tą trasę tylko po jej wygenerowaniu")
        if self._current_route is not None:
            try:
                stop_start = self._stop_model.get_stop_by_id(self._current_route.start_stop_id)
                stop_end = self._stop_model.get_stop_by_id(self._current_route.destination_stop_id)
                if (stop_start == stop_end):
                    self.show_message_box("Uwaga!", "Przystanki startowy i końcowy nie mogą być tym samym przystankiem!")
                    return
                self._user_config.add_favourite_route(group, self._current_route)
            except:
                self.show_message_box("Uwaga!", "Nie można zapisać trasy bez żadnego przystanku")

    def get_tuple_from_str(self, str):
        myStr = str
        myStr = myStr.replace("(", "")
        myStr = myStr.replace(")", "")
        myStr = myStr.replace(",", " ")
        myList = myStr.split()
        myList = list(map(float, myList))
        return tuple(myList)

    def _on_search(self, route=None):
        # clear map
        self.map_model.create_map()
        try:
            if (route != None):
                object_id_start, object_id_end = route.start_stop_id, route.destination_stop_id
                object_type_start, object_type_end = STOP_OBJECT_TYPE, STOP_OBJECT_TYPE
            else:
                try:
                    object_type_start, object_id_start = self._stop_model.parse_readable_identifier(self._ui.searchBar1.text())
                except:
                    object_type_start, object_id_start = STOP_OBJECT_TYPE, self.get_tuple_from_str(self._ui.searchBar1.text())
                
                try:
                    object_type_end, object_id_end = self._stop_model.parse_readable_identifier(self._ui.searchBar2.text())
                except:
                    myStr = self._ui.searchBar2.text()
                    myStr = myStr.replace("(", "")
                    myStr = myStr.replace(")", "")
                    myStr = myStr.replace(",", " ")
                    myList = myStr.split()
                    myList = list(map(float, myList))
                    myTuple = tuple(myList)
                    object_type_end, object_id_end = STOP_OBJECT_TYPE, self.get_tuple_from_str(self._ui.searchBar2.text())
                
            selected_time = datetime.combine(date.min, self._ui.timeEdit.time().toPython())
            
            self._nav_steps_thread = NavStepsDownload(self._astar_model, selected_time, object_id_start, object_id_end)
            self._nav_steps_thread.finished.connect(functools.partial(self._on_nav_steps_complete, object_type_start, object_type_end))
            self._nav_steps_thread.start()

        except ValueError as e:
            logging.error(e)


    def _on_nav_steps_complete(self, object_type_start, object_type_end, highlighted_stop_ids = [], highlighted_stop_color="black"):
        self._nav_steps = self._nav_steps_thread.nav_steps
        if (self._nav_steps == None):
            self.show_message_box("Uwaga!", "Przystanki startowy i końcowy nie mogą być tym samym przystankiem!")
            return
        object_id_start = self._nav_steps[0].start_node.stop.stop_id
        object_id_end = self._nav_steps[len(self._nav_steps)-1].destination_node.stop.stop_id
        if (object_id_start == -2 or object_id_start == -1):
            object_id_start = self._nav_steps[0].destination_node.stop.stop_id
        if (object_id_end == -1 or object_id_end == -2):
            object_id_end = self._nav_steps[len(self._nav_steps)-1].start_node.stop.stop_id
        self._current_route = NavRoute(object_id_start, object_id_end)
        self.show_stops_list()#self._inter_stops)

        if (len(highlighted_stop_ids) == 0):
            self.map_model.create_map(self.map_model.calculate_average_focus([stop.get_location() for stop in self._inter_stops]))
        else:
            try: # if it's a stop
                start_stop_location = self._stop_model.get_stop_by_id(highlighted_stop_ids[0]).get_location()
            except:
                start_stop_location = self._nav_steps[0].start_node.stop.get_location()
            try: # if it's a stop
                end_stop_location = self._stop_model.get_stop_by_id(highlighted_stop_ids[1]).get_location()
            except:
                end_stop_location = self._nav_steps[len(self._nav_steps)-1].destination_node.stop.get_location()
            self.map_model.create_map(self.map_model.calculate_average_focus([loc for loc in [start_stop_location, end_stop_location]]), 15)

        if object_type_start == STOP_OBJECT_TYPE:
            logging.info("This is a stop!")
            try: # if it's a stop
                stop_start = self._stop_model.get_stop_by_id(object_id_start)
                self.map_model.show_stop(stop_start)
            except: # if it's a location
                self.map_model.show_location(self._nav_steps[0].start_node.stop.get_location())
        else:
            raise ValueError(f"Invalid object type {object_type_start}")

        if object_type_end == STOP_OBJECT_TYPE:
            logging.info("This is a stop!")
            try: # if it's a stop
                stop_end = self._stop_model.get_stop_by_id(object_id_end)
                self.map_model.show_stop(stop_end)
            except: # if it's a location
                self.map_model.show_location(self._nav_steps[len(self._nav_steps)-1].destination_node.stop.get_location())
        else:
            raise ValueError(f"Invalid object type {object_type_end}")


        last_line_taken = None
        last_line_type_taken = None

        last_bus_color = "blue"
        last_train_color = "red"
        last_tram_color = "green"
        stops = [n.start_node.stop for n in self._nav_steps]
        stops.append(self._nav_steps[-1:][0].destination_node.stop)
        self.map_model.show_stops(stops, "orange", "red", "purple", highlighted_stop_ids, highlighted_stop_color)
    
        for nav_step in self._nav_steps:

            if (isinstance(nav_step, GoOnFoot)):
                self.map_model.show_line_path([
                    tuple([nav_step.start_node.stop.latitude, nav_step.start_node.stop.longitude]),
                    tuple([nav_step.destination_node.stop.latitude, nav_step.destination_node.stop.longitude])
                ], "black", '7')
                last_line_taken = None
                last_line_type_taken = None
            elif (isinstance(nav_step, TakeTransit)):
                inter_stops_ids = []
                for single_course in nav_step.start_node.line_variant_courses[nav_step.line_variant]:
                    if (nav_step.start_node.stop.stop_id in single_course.variant_stops.ordered_stop_ids and
                    nav_step.destination_node.stop.stop_id in single_course.variant_stops.ordered_stop_ids):
                        left_index = single_course.variant_stops.ordered_stop_ids.index(nav_step.start_node.stop.stop_id)
                        right_index = single_course.variant_stops.ordered_stop_ids.index(nav_step.destination_node.stop.stop_id)+1
                        inter_stops_ids = single_course.variant_stops.ordered_stop_ids[left_index:right_index]
                        break

                line_type = self._line_model._get_line_type_by_variant_id(nav_step.line_variant).name
                line_id = self._line_model._get_line_by_variant_id(nav_step.line_variant).name
                # green -> tram
                # blue -> bus
                # red -> train
                if (last_line_type_taken == line_type and last_line_taken != line_id):
                    if (line_type == "LINIA TRAMWAJOWA" or line_type == "LINIA TRAMWAJOWA UZUPEŁNIAJĄCA"): # tram
                        if (last_tram_color == "green"): color = "#4b9b7f"
                        else: color = "green"
                        last_tram_color = color
                    elif (line_type == "LINIA KOLEI MIEJSKIEJ"): # train
                        if (last_train_color == "red"): color = "#dc4a1f"
                        else: color = "red"
                        last_train_color = color
                    else: # bus
                        if (last_bus_color == "blue"): color = "#7eeef3"
                        else: color = "blue"
                        last_bus_color = color
                else:
                    if (line_type == "LINIA TRAMWAJOWA" or line_type == "LINIA TRAMWAJOWA UZUPEŁNIAJĄCA"): # tram
                        color = "green"
                        last_tram_color = color
                    elif (line_type == "LINIA KOLEI MIEJSKIEJ"): # train
                        color = "red"
                        last_train_color = color
                    else: # bus
                        color = "blue"
                        last_bus_color = color

                for i in range(len(inter_stops_ids)-1):
                    stop_start = self._stop_model.get_stop_by_id(inter_stops_ids[i])
                    stop_end = self._stop_model.get_stop_by_id(inter_stops_ids[i+1])
                    self.map_model.show_line_path([
                    tuple([stop_start.latitude, stop_start.longitude]),
                    tuple([stop_end.latitude, stop_end.longitude])
                ], color, '1') 

                # self.map_model.show_line_path([
                #     tuple([nav_step.start_node.stop.latitude, nav_step.start_node.stop.longitude]),
                #     tuple([nav_step.destination_node.stop.latitude, nav_step.destination_node.stop.longitude])
                # ], color, '1') 

                last_line_type_taken = line_type
                last_line_taken = line_id

        self._ui.webMap.setHtml(self.map_model.map.get_root().render())


    def clearlayout(self, layout):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).setParent(None)
            layout.removeItem(layout.itemAt(i))
            layout.itemAt(i).show()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NavigationLayout()
    window.show()
    app.exec()