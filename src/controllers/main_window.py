import logging

from src.views.ui_main_window import Ui_MainWindow

from src.models.user_config_model import UserConfigModel

from src.controllers.stop_layout import StationLayout

from src.controllers.navigation_layout import NavigationLayout

from src.controllers.lines_layout import LinesLayout

from src.core.controller import Controller

from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QMessageBox


from PySide6.QtWidgets import QWidget, QCompleter, QApplication, QHBoxLayout, QVBoxLayout, QPushButton #
import PySide6.QtCore as QtCore #
from PySide6.QtGui import QIcon
from pathlib import Path

class MainWindow(Controller, QMainWindow):
    def __init__(self, app) -> None:
        super().__init__()

        self._ui = Ui_MainWindow()
        self._ui.setupUi(self)

        self._app = app

        # Models
        self._user_config = UserConfigModel.get_instance()
        self._user_config.load()

        self._ui_finalize()
        self._set_up_triggers()


    def _set_up_triggers(self):
        pass


    def _ui_finalize(self):
        # Lines layout tab
        self._ui.tLinie.setLayout(QVBoxLayout())

        self._lines_layouts_widget = LinesLayout(self)
        self._ui.tLinie.layout().addWidget(self._lines_layouts_widget)
        self.previous_uis = []
        self.previous_uis.append(self._lines_layouts_widget)

        # Station layout tab
        self._ui.tUklady.setLayout(QVBoxLayout())
        self._station_layouts_widget = StationLayout()
        self._ui.tUklady.layout().addWidget(self._station_layouts_widget)

        # Navigation layout tab
        self._ui.tNavigation.setLayout(QVBoxLayout())
        self._navigation_layouts_widget = NavigationLayout()
        self._ui.tNavigation.layout().addWidget(self._navigation_layouts_widget)


    def closeEvent(self, event) -> None:
        if self._user_config.has_changed():
            ans = QMessageBox.question(self, "Czekaj!", "Czy chcesz zapisać ustawienia użytkownika?")
            if ans == QMessageBox.StandardButton.Yes:
                logging.info("Saving user config!")
                self._user_config.save()
        return super(MainWindow, self).closeEvent(event)


    def change_lines_widget(self, new_widget): #! Move this func to somewhere else, maybe, idk
        for i in reversed(range(self._ui.tLinie.layout().count())): 
            self._ui.tLinie.layout().itemAt(i).widget().setParent(None)
        self._lines_layouts_widget = new_widget

        if (new_widget not in self.previous_uis):
            self.previous_uis.append(new_widget)

        if (len(self.previous_uis) > 1):

            qbtn = QPushButton('Powrót', self)
            icon = QIcon(str(Path().absolute())+"/Assets/back_icon.png".format("file_important"))
            qbtn.setIcon(icon)
            qbtn.clicked.connect(lambda : self.on_back_button())
            qbtn.resize(qbtn.sizeHint())
            self._ui.tLinie.layout().addWidget(qbtn, 1, alignment=QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)

        self._ui.tLinie.layout().addWidget(self._lines_layouts_widget, 100)
        


    def on_back_button(self):
        self.previous_uis.pop()
        self.change_lines_widget(self.previous_uis[len(self.previous_uis)-1])