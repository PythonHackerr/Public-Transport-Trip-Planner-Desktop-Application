from src.core.custom_types import *
from PySide6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
import folium


def show_geopoints_on_map(geopoints: list[Geopoint_t]):
    map = folium.Map()

    for geopoint in geopoints:
        folium.Marker(geopoint).add_to(map)

    webMap = QWebEngineView()
    webMap.setHtml(map.get_root().render())

    return webMap


def generate_chunk_corners(n_of_chunks):
    all_geopoints = []
    lat_min, lng_min, lat_span, lng_span = 51.921869, 20.462591, 0.561141, 1.001192
    for x in range(n_of_chunks+1):
        for y in range(n_of_chunks+1):
            all_geopoints.append((lat_min + lat_span * x / n_of_chunks, lng_min + lng_span * y / n_of_chunks))

    return all_geopoints

def main():
    app = QApplication()
    points = generate_chunk_corners(32)
    webmap = show_geopoints_on_map(points)
    layout = QHBoxLayout()
    layout.addWidget(webmap)

    widget = QWidget()
    widget.setLayout(layout)
    widget.show()
    app.exec()


if __name__ == "__main__":
    main()
