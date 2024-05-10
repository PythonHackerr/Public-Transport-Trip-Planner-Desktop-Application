from PySide6.QtCore import Signal
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QApplication
import folium
import folium.plugins
import logging
from src.views.console_handling_web_page import ConsoleHandlingWebPage
from src.core.custom_types import Geopoint_t


class PickLocationOnMap(QWebEngineView):
    """
    Map widget that allows for selection of a location on the map by clicking on it. Location is sent with a signal.
    """
    location_ready = Signal(tuple)

    def __init__(self, fmap: folium.Map, parent=None):
        super().__init__(parent)
        self._map = fmap
        folium.LatLngPopup().add_to(self._map)

        self._page = ConsoleHandlingWebPage(self)
        self.setPage(self._page)
        self.setHtml(self._map.get_root().render())
        self._page.console_message_recieved.connect(self._on_console_message)

    def init_location_query(self):
        # Literally java script :(
        self._page.runJavaScript(
            """
            var full_var_name
            for(var name in this)
            {
                if(name.startsWith("lat_lng_"))
                {
                    full_var_name = name
                }
            }
            lat = this[full_var_name].getLatLng()["lat"]
            lng = this[full_var_name].getLatLng()["lng"]
            console.log(lat, lng)
            """
        )
        logging.info("Init location query")

    def _on_console_message(self, msg):
        try:
            latlng = tuple(map(float, msg.split(" ")))
            logging.info(f"Location retrieval successful: {latlng}")
            self.location_ready.emit(latlng)
        except ValueError:
            pass
        except Exception as e:
            raise e


def main():
    logging.basicConfig(format="[%(asctime)s->%(levelname)s->%(module)s" +
                               "->%(funcName)s]: %(message)s",
                        datefmt="%H:%M:%S",
                        level=logging.INFO)
    app = QApplication()
    layout = QVBoxLayout()
    fmap = folium.Map()
    nav = PickLocationOnMap(fmap)
    button = QPushButton("Uzyskaj lokalizację")
    button.clicked.connect(nav.init_location_query)

    nav.location_ready.connect(print)

    layout.addWidget(nav)
    layout.addWidget(button)

    widget = QWidget()
    widget.setLayout(layout)
    widget.show()
    app.exec()


if __name__ == "__main__":
    main()
