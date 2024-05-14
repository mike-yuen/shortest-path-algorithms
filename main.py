import sys
import os

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QWidget, QGroupBox,
    QRadioButton, QVBoxLayout, QHBoxLayout, QFileDialog, QSizePolicy, QToolTip
)
from PySide6.QtCore import QUrl, QPointF
from PySide6.QtGui import QFont, QPainter
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCharts import QChartView, QChart, QLineSeries, QScatterSeries

import process_map_data as pmd


def generate_map_html(path):
    """
    Generate HTML content with dynamic path input.

    Args:
    - path (list of tuples): List of (latitude, longitude) tuples representing the path.

    Returns:
    - str: The HTML content with dynamic path input.
    """
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>OpenStreetMap with Path</title>
        <script src="https://cdn.jsdelivr.net/npm/leaflet@1.7.1/dist/leaflet.js"></script>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.7.1/dist/leaflet.css" />
        <style>
            #map {{ height: 100vh; }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            var map = L.map('map').setView([{path[0][0]}, {path[0][1]}], 13); // Set initial view
            L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '© OpenStreetMap contributors'
            }}).addTo(map); // Add OSM layer

            // Function to add path to the map
            function addPath(path) {{
                var latLngs = [];
                path.forEach(function(node) {{
                    latLngs.push(L.latLng(node[0], node[1]));
                }});
                var polyline = L.polyline(latLngs, {{color: 'blue'}}).addTo(map);
                map.fitBounds(polyline.getBounds()); // Adjust map view to fit the path
            }}

            // Example path (replace with your path)
            var path = [
    """

    for lat, lon in path:
        html_content += f"                [{lat}, {lon}],\n"

    html_content += """
            ];

            // Call the addPath function with the path
            addPath(path);
        </script>
    </body>
    </html>
    """
    return html_content


def generate_bounding_box_map_html(bounds: list):
    view = [(bounds[0][0] + bounds[1][0]) / 2, (bounds[0][1] + bounds[1][1]) / 2]
    html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>OpenStreetMap Bounding Box</title>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
            <style>
                #map {{ height: 500px; }}
            </style>
        </head>
        <body>
    
        <div id="map"></div>
    
        <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
        <script>
            var map = L.map('map').setView([{view[0]}, {view[1]}], 15);
    
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }}).addTo(map);
    
            var bounds = {str(bounds)};
            L.rectangle(bounds, {{color: "#ff7800", weight: 1}}).addTo(map);
        </script>
    
        </body>
        </html>
    """
    return html


class WebEngineView(QWidget):
    def __init__(self, html_content, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        browser = QWebEngineView()
        browser.setHtml(html_content)
        layout.addWidget(browser)
        self.setLayout(layout)


class Application(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenStreetMap with Path")
        # loaded variables
        self.reader = None
        #
        widget = QWidget()
        layout = QVBoxLayout(widget)
        algorithm_group_box = QGroupBox()
        algorithm_group_box.setTitle('Algorithms')
        algorithm_group_box.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        algorithm_selection_layout = QHBoxLayout(algorithm_group_box)
        dijkstra_radio_btn = QRadioButton(self)
        dijkstra_radio_btn.setText('Dijkstra')
        bellman_radio_btn = QRadioButton(self)
        bellman_radio_btn.setText('Bellman-Ford')
        floyd_radio_btn = QRadioButton(self)
        floyd_radio_btn.setText('Floyd-Warshall')
        algorithm_selection_layout.addWidget(dijkstra_radio_btn)
        algorithm_selection_layout.addWidget(bellman_radio_btn)
        algorithm_selection_layout.addWidget(floyd_radio_btn)
        # chart and web view
        chart_and_web_widget = QWidget()
        self.chart_web_layout = QHBoxLayout(chart_and_web_widget)
        self.view_left = None
        self.view_right = None
        # execute buttons
        open_osm_btn = QPushButton('Open OSM File', self)
        open_osm_btn.clicked.connect(self.load_osm_file)
        show_result_btn = QPushButton('Show Result', self)
        show_result_btn.clicked.connect(self.run_shortest_path_algorithm)
        verify_result_btn = QPushButton('Verify with Online Map', self)
        # add widgets
        layout.addWidget(chart_and_web_widget)
        layout.addWidget(algorithm_group_box)
        layout.addWidget(open_osm_btn)
        layout.addWidget(show_result_btn)
        layout.addWidget(verify_result_btn)
        self.setCentralWidget(widget)
        self.showMaximized()

    def run_shortest_path_algorithm(self):
        if self.reader is not None:
            path = [(10.7622564, 106.6569704),
                    (10.7621586, 106.6570011),
                    (10.7689823, 106.6525092),
                    (10.7694154, 106.6525035),
                    (10.7711526, 106.6529604),
                    (10.7704293, 106.6577405),
                    ]
            web_viewer = WebEngineView(
                html_content=generate_map_html(path), parent=self)
            web_viewer1 = QWebEngineView()
            start_lat, start_lon = 10.7857536, 106.6669098
            end_lat, end_lon = 10.7713016, 106.6578284
            # Generate a URL to display the route using OpenStreetMap
            route_url = f"https://www.openstreetmap.org/directions?engine=fossgis_osrm_car&route={start_lat}%2C{start_lon}%3B{end_lat}%2C{end_lon}"
            # Load the URL in the web engine view
            web_viewer1.load(QUrl(route_url))
            self.chart_web_layout.replaceWidget(self.view_left, web_viewer)
            self.chart_web_layout.replaceWidget(self.view_right, web_viewer1)

    def load_osm_file(self):
        filepath = QFileDialog.getOpenFileName(self, "Open File", "/home", "OSM file (*.osm)")
        if os.path.isfile(filepath[0]):
            self.reader = pmd.OSMReader.parse(filepath[0])
            chart = QChart()
            scatter_series = QScatterSeries()
            scatter_series.setMarkerSize(10.0)
            for line in self.reader.get_coords_for_chart():
                series = QLineSeries()
                for node in line:
                    series.append(*node)
                    scatter_series.append(*node)
                chart.addSeries(series)
                chart.addSeries(scatter_series)
            scatter_series.hovered.connect(self.on_hover)
            chart.legend().hide()
            chart.createDefaultAxes()
            chart.setTitle("Simple Line Chart")
            chart.createDefaultAxes()
            self.view_left = QChartView(chart)
            self.view_left.setMouseTracking(True)
            # Enable rubber band for zooming
            self.view_left.setRubberBand(QChartView.RectangleRubberBand)
            self.view_left.setDragMode(QChartView.ScrollHandDrag)
            self.view_left.setRenderHint(QPainter.Antialiasing)
            self.view_right = WebEngineView(
                html_content=generate_bounding_box_map_html(self.reader.get_array_bounds()))
            self.chart_web_layout.addWidget(self.view_left)
            self.chart_web_layout.addWidget(self.view_right)

    def on_hover(self, point, state):
        if state:
            QToolTip.setFont(QFont('SansSerif', 10))
            QToolTip.showText(self.view_left.mapToGlobal(
                self.view_left.mapFromScene(QPointF(point.x(), point.y()))),
                              f'({point.x()}, {point.y()})')
        else:
            QToolTip.hideText()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Application()
    sys.exit(app.exec())
