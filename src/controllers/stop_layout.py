import functools
import logging
import sys
import folium
from PySide6.QtGui import QAction
from src.models.user_config_model import UserConfigModel
from src.models.stop_model import Stop, StopComplex, StopModel, STOP_COMPLEX_OBJECT_TYPE, STOP_OBJECT_TYPE
from src.core.controller import Controller
from src.views.ui_stop_layout import Ui_WidgetStopComplex
from src.core.constants import DEFAULT_LOC_WARSAW
from PySide6.QtWidgets import QWidget, QCompleter, QApplication, QTreeWidgetItem, QListWidgetItem, QMenu, QInputDialog, \
    QMessageBox
from PySide6.QtCore import QStringListModel, Qt, QThread, QSize
from PySide6.QtGui import QAction, QIcon, QPixmap
from pathlib import Path


class FavouritesGroup(QTreeWidgetItem):
    def __init__(self, group_name, isRoutes=False):
        super().__init__()
        self._name = group_name
        self.setText(0, self._name)
        self.setFlags(self.flags() | Qt.ItemFlag.ItemIsEditable)
        self._isRoutes = isRoutes
        self._user_config = UserConfigModel.get_instance()

    def setData(self, column: int, role: int, value) -> None:
        if role == Qt.ItemDataRole.EditRole:
            if self._name != value:
                logging.info(f"Group {self._name} changed name to {value}")
                if (self._isRoutes):
                    self._user_config.rename_routes_group(self._name, value)
                else:
                    self._user_config.rename_group(self._name, value)
                self._name = value
        super().setData(column, role, value)

    def get_name(self):
        return self._name


class StopComplexTreeItem(QTreeWidgetItem):
    def __init__(self, group: FavouritesGroup, stop_complex: StopComplex):
        super().__init__(group)

        self.setText(0, str(stop_complex))
        self._complex = stop_complex
        self._group = group

    def get_complex(self):
        return self._complex

    def get_group(self):
        return self.parent().get_name()


class StopListItem(QListWidgetItem):
    def __init__(self, stop: Stop):
        super().__init__()

        self.setText(str(stop))
        self._stop = stop

    def get_stop(self):
        return self._stop


class ComplexesAndStopsDownload(QThread):
    def __init__(self, stop_model: StopModel):
        super().__init__()
        self._stop_model = stop_model

        self.stops = None
        self.complexes = None

    def run(self) -> None:
        self.complexes = self._stop_model.get_complexes()
        logging.info("Complex download complete")
        self.stops = self._stop_model.get_all_stops()
        logging.info("Stops download complete")


class StationLayout(Controller, QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ui = Ui_WidgetStopComplex()
        self._ui.setupUi(self)
        self._ui.webMap.hide()

        self.setDisabled(True)
        # Models
        self._user_config = UserConfigModel.get_instance()
        self._stop_model = StopModel()

        self._download_thread = ComplexesAndStopsDownload(self._stop_model)
        self._download_thread.finished.connect(self._on_init_data_download_complete)
        self._download_thread.start()

    def _on_init_data_download_complete(self):
        logging.info("All initial downloads are complete!")
        self._current_complex: StopComplex = None
        self._fav_menu = None

        self._stop_complex_names_qmodel = QStringListModel()
        stop_identifiers = [stop.readable_identifier for stop in self._download_thread.stops]
        complex_identifiers = [complex.readable_identifier for complex in self._download_thread.complexes]

        self._stop_complex_names_qmodel.setStringList(stop_identifiers + complex_identifiers)
        #####

        self._search_bar_completer = QCompleter()
        self._search_bar_completer.setModel(self._stop_complex_names_qmodel)
        self._search_bar_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._search_bar_completer.setFilterMode(Qt.MatchFlag.MatchContains)

        self._ui_finalize()
        self._set_up_triggers()
        self.setEnabled(True)

    def _set_up_triggers(self):
        # Search complex of given string identifier on enter pressed
        self._ui.leSearchBar.returnPressed.connect(self._on_search)
        # Remove selected items from favourites
        self._ui.btRemoveFav.clicked.connect(self._on_favourite_delete)
        # Jump to a complex from favourites on double click
        self._ui.lsFavourites.itemDoubleClicked.connect(self._on_jump_to_favourite)
        # When favourites are updated...
        self._user_config.favourites_updated.connect(self._reload_favourites)
        self._user_config.groups_updated.connect(self._reload_fav_button)
        # Focus on a stop from complex stops on double click
        self._ui.lsComplexStops.itemDoubleClicked.connect(self._on_stop_focus)
        # Add new group button press
        self._ui.btNewGroup.clicked.connect(self._on_new_group)

        pixmap = QPixmap((str(Path().absolute())+"/Assets/add_icon.png".format("file_important")))
        icon = QIcon(pixmap)
        self._ui.btNewGroup.setIcon(icon)
        self._ui.btNewGroup.setIconSize(QSize(20,22))

        pixmap = QPixmap((str(Path().absolute())+"/Assets/remove_icon.png".format("file_important")))
        icon = QIcon(pixmap)
        self._ui.btRemoveFav.setIcon(icon)
        self._ui.btRemoveFav.setIconSize(QSize(20,22))

        pixmap = QPixmap((str(Path().absolute())+"/Assets/remove_icon.png".format("file_important")))
        icon = QIcon(pixmap)
        self._ui.btRemoveFav.setIcon(icon)
        self._ui.btRemoveFav.setIconSize(QSize(20,22))

        icon = QIcon(str(Path().absolute())+"/Assets/save_icon.png".format("file_important"))
        self._ui.btFavourite.setIcon(icon)


    def _ui_finalize(self):
        self._ui.leSearchBar.setCompleter(self._search_bar_completer)
        self._reload_favourites()
        self._reload_fav_button()

    def _on_new_group(self):
        ret = QInputDialog.getText(self, "Nowa grupa", "Nowa nazwa grupy")
        group, success = ret
        if success:
            try:
                self._user_config.add_new_group(group)
                logging.info(f"Adding new favourite group: {group}")
                self._reload_favourites()
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))

    def _on_search(self):
        selection = self._ui.leSearchBar.text()
        # Find the right stop_complex info
        stop_complex = None
        try:
            object_type, object_id = self._stop_model.parse_readable_identifier(selection)
            if object_type == STOP_COMPLEX_OBJECT_TYPE:
                stop_complex = self._stop_model.get_complex_by_id(object_id)
                self.show_stop_complex(stop_complex)
            elif object_type == STOP_OBJECT_TYPE:
                logging.info("This is a stop!")
                stop_complex = self._stop_model.get_complex_by_stop_id(object_id)
                stop = self._stop_model.get_stop_by_id(object_id)
                self.show_stop_complex(stop_complex, stop)
            else:
                raise ValueError(f"Invalid object type {object_type}")
        except ValueError as e:
            logging.error(e)

    def _on_jump_to_favourite(self, selection: QTreeWidgetItem):
        if isinstance(selection, StopComplexTreeItem):
            self.show_stop_complex(selection.get_complex())

    def _on_favourite_delete(self):
        selection = self._ui.lsFavourites.selectedItems()

        groups = []
        removal_list = []
        for item in selection:
            if isinstance(item, FavouritesGroup):
                groups.append(item.get_name())
            elif isinstance(item, StopComplexTreeItem):
                removal_list.append((item.get_group(), item.get_complex().stop_complex_id))

        self._user_config.remove_groups(groups, no_emit=True)
        self._user_config.remove_favourite_complexes(removal_list)

    def _reload_favourites(self):
        self._ui.lsFavourites.setSortingEnabled(False)
        self._ui.lsFavourites.clear()
        for group in self._user_config.get_favourite_complexes():
            group_item = FavouritesGroup(group)
            self._ui.lsFavourites.addTopLevelItem(group_item)
            for complex_id in self._user_config.get_favourites_by_group(group):
                stop_complex = self._stop_model.get_complex_by_id(complex_id)
                item = StopComplexTreeItem(group_item, stop_complex)
        self._ui.lsFavourites.setSortingEnabled(True)

    def _reload_stops(self, stops):
        self._ui.lsFavourites.setSortingEnabled(False)
        self._ui.lsComplexStops.clear()
        for stop in stops:
            item = StopListItem(stop)
            self._ui.lsComplexStops.addItem(item)
        self._ui.lsFavourites.setSortingEnabled(True)

    def _add_current_complex_to_favourites(self, group):
        if self._current_complex is not None:
            self._user_config.add_favourite_complex(group, self._current_complex.stop_complex_id)

    def _reload_fav_button(self):
        self._fav_menu = QMenu()
        self._fav_menu_actions = []
        for group in self._user_config.get_groups():
            action = QAction()
            action.setText(group)
            action.triggered.connect(functools.partial(self._add_current_complex_to_favourites, group=group))
            self._fav_menu.addAction(action)
            self._fav_menu_actions.append(action)

        if len(self._fav_menu_actions) == 0:
            no_groups_prompt = QAction()
            no_groups_prompt.setText("Najpierw musisz stworzyć grupę!")
            no_groups_prompt.setDisabled(True)
            self._fav_menu.addAction(no_groups_prompt)
            self._fav_menu_actions.append(no_groups_prompt)
        self._ui.btFavourite.setMenu(self._fav_menu)

    def _on_stop_focus(self, selection: StopListItem):
        self.show_stop_complex(self._current_complex, selection.get_stop())

    def show_stop_complex(self, stop_complex: StopComplex, highlighted_stop: Stop = None):
        # Show web frame if still hidden
        if self._ui.webMap.isHidden():
            self._ui.webMap.setHidden(False)
            w = self.geometry().width()
            self._ui.spLeftRight.setSizes([w * 0.60, w * 0.40])
        self._ui.lbComplexPrompt.setText(str(stop_complex))

        logging.info(f"Showing {stop_complex}")

        # Save currently displayed complex
        self._current_complex = stop_complex

        # Get complex stops
        complex_stops = self._stop_model.get_stops_of_stop_complex(stop_complex.stop_complex_id)
        n_stops = len(complex_stops)

        if n_stops == 0:
            logging.warning(f"{stop_complex} has no stops")
            return

        # reload the complex stops table
        self._reload_stops(complex_stops)

        map_focus, zoom = self.calculate_map_focus_and_zoom(complex_stops, highlighted_stop, stop_complex)
        mapa = folium.Map(location=map_focus, zoom_start=zoom)

        self.put_markers_on_stops(complex_stops, highlighted_stop, mapa)

        self._ui.webMap.setHtml(mapa.get_root().render())

    def put_markers_on_stops(self, complex_stops, highlighted_stop, mapa):
        # Put markers on all stops
        for stop in complex_stops:
            if not stop.has_location():
                continue
            loc = stop.latitude, stop.longitude
            if highlighted_stop is not None and stop == highlighted_stop:
                folium.Marker(loc, None, tooltip=str(stop), parse_html=True, icon=folium.Icon(color='red')).add_to(mapa)
            else:
                folium.Marker(loc, None, tooltip=str(stop), parse_html=True).add_to(mapa)

    def calculate_map_focus_and_zoom(self, complex_stops, highlighted_stop, stop_complex):
        # focus on the selected one or just the average
        if highlighted_stop is None:
            lat_sum, lon_sum = 0, 0
            n_stops_with_loc = 0
            for stop in complex_stops:
                if stop.has_location():
                    n_stops_with_loc += 1
                    lat_sum += stop.latitude
                    lon_sum += stop.longitude
            if n_stops_with_loc > 0:
                lat_sum /= n_stops_with_loc
                lon_sum /= n_stops_with_loc
                map_focus = (lat_sum, lon_sum)
                zoom = 16
            else:
                logging.info(f"No stops of {stop_complex} have locations")
                map_focus = DEFAULT_LOC_WARSAW
                zoom = 12
        elif highlighted_stop.has_location():
            map_focus = (highlighted_stop.latitude, highlighted_stop.longitude)
            zoom = 18
        elif not highlighted_stop.has_location():
            logging.info(f"Highlighted stop {highlighted_stop} has no location")
            map_focus = DEFAULT_LOC_WARSAW
            zoom = 12
        return map_focus, zoom


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StationLayout(None)
    window.show()
    app.exec()
