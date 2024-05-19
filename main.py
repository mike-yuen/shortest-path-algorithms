import sys
import typing as tp
import scipy.spatial as sp
import os
import numpy as np
import process_map_data as pmd
import dijkstra
import bellman_ford

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QWidget, QGroupBox,
    QRadioButton, QVBoxLayout, QHBoxLayout, QFileDialog, QSizePolicy,
    QGraphicsSimpleTextItem, QDialog
)
from PySide6.QtCore import QPointF, QObject, Signal, Qt, QUrl
from PySide6.QtGui import QPainter, QBrush, QPen, QFont
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCharts import QChartView, QChart, QLineSeries, QScatterSeries
from jinja2 import Environment, FileSystemLoader

# variables
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
env = Environment(loader=FileSystemLoader(CURRENT_DIR))
TEMPLATE = env.get_template('map_template.html')


class WebEngineView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        self._browser = QWebEngineView(self)
        layout.addWidget(self._browser)
        self.setLayout(layout)

    def set_html_content(self, html: str):
        self._browser.setHtml(html)

    def load(self, url: str):
        self._browser.load(QUrl(url))


class ScatterCommunicator(QObject):
    node_clicked_signal = Signal(int)


class ChartView(QWidget):
    def __init__(self, title=None, parent=None):
        super().__init__(parent)
        self._title = title
        self._scatter_series = QScatterSeries()
        self._scatter_series.setMarkerSize(5)
        self._scatter_series.hovered.connect(self.on_hovered)
        self._chart_view = QChartView()
        self._chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        #
        layout = QHBoxLayout()
        layout.addWidget(self._chart_view)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        # signals
        self._communicator = ScatterCommunicator()
        self.nodeClicked = self._communicator.node_clicked_signal
        #
        self._chart = None
        self._points = None
        self._kdtree = None
        self._highlighted_series = None
        self._labels = []
        self._selected_series = QScatterSeries()
        self._node_infos = None

    def plot(self, points: np.ndarray):
        assert points.shape[1] == 2
        self._chart = QChart()
        self._chart.legend().hide()
        if self._title is not None:
            self._chart.setTitle(self._title)
        #
        for nodes in points:
            line_series = QLineSeries()
            for point in nodes:
                line_series.append(*point)
            self._chart.addSeries(line_series)
        self._chart.createDefaultAxes()
        self._chart.axes()[0].hide()
        self._chart.axes()[1].hide()
        self._chart_view.setChart(self._chart)

    def scatter(self, points: np.ndarray, node_infos=None):
        assert points.shape[1] == 2
        if self._points is None:
            self._points = points
        self._kdtree = sp.KDTree(points)
        for index, point in enumerate(points):
            self._scatter_series.append(*point)
        self._chart.addSeries(self._scatter_series)
        self._node_infos = node_infos

    def on_node_clicked(self, point: QPointF):
        if self._kdtree is None:
            return
        if self._selected_series:
            if len(self._selected_series.points()) == 2:
                self._chart.removeSeries(self._selected_series)
                self._selected_series = QScatterSeries()
        if len(self._labels) >= 2:
            for label in self._labels:
                self._chart.scene().removeItem(label)
            self._labels.clear()
        x = point.x()
        y = point.y()
        node_index = self._kdtree.query([x, y], k=1)[1]
        self._selected_series.append(point)
        label = QGraphicsSimpleTextItem(f'({self._node_infos[node_index][0]},\n'
                                        f'{self._node_infos[node_index][1]})')
        font = QFont()
        font.setPointSize(13)
        label.setFont(font)
        label.setBrush(QBrush(Qt.GlobalColor.black))
        self._labels.append(label)
        pos = self._chart.mapToPosition(point, self._scatter_series)
        label.setPos(pos.x(), pos.y())
        self._chart.scene().addItem(label)
        self._selected_series.setMarkerSize(10)
        self._selected_series.setBrush(QBrush(Qt.GlobalColor.green))
        self._selected_series.setPen(QPen(Qt.GlobalColor.black))
        self._chart.addSeries(self._selected_series)
        self._chart.createDefaultAxes()
        self._chart.axes()[0].hide()
        self._chart.axes()[1].hide()
        self.nodeClicked.emit(node_index)

    def on_hovered(self, point: QPointF):
        if self._highlighted_series:
            self._chart.removeSeries(self._highlighted_series)
        self._highlighted_series = QScatterSeries()
        self._highlighted_series.clicked.connect(self.on_node_clicked)
        self._highlighted_series.append(point)
        self._highlighted_series.setMarkerSize(10)
        self._highlighted_series.setBrush(QBrush(Qt.GlobalColor.yellow))
        self._highlighted_series.setPen(QPen(Qt.GlobalColor.black))
        self._chart.addSeries(self._highlighted_series)
        self._chart.createDefaultAxes()
        self._chart.axes()[0].hide()
        self._chart.axes()[1].hide()

    def reset(self):
        self._scatter_series.clear()
        self._chart = None
        self._points = None
        self._kdtree = None
        self._highlighted_series = None
        self._labels = []
        self._selected_series.clear()
        self._node_infos = None


class OnlineMapDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self._web_view = WebEngineView()
        layout.addWidget(self._web_view)
        self.setLayout(layout)
        self.setWindowTitle('Online Map')
        self.setMinimumSize(720, 480)

    def find_best_way(self, start_loc: list, end_loc: list):
        # Generate a URL to display the route using OpenStreetMap
        route_url = (f"https://www.openstreetmap.org/directions?"
                     f"engine=graphhopper_foot"
                     f"&route={start_loc[0]}%2C{start_loc[1]}%3B{end_loc[0]}%2C{end_loc[1]}")
        self._web_view.load(route_url)


class Application(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenStreetMap with Path")
        self.reader = None
        self.index_to_marker_positions = {}
        #
        widget = QWidget()
        layout = QVBoxLayout(widget)
        algorithm_group_box = QGroupBox()
        algorithm_group_box.setTitle('Algorithms')
        algorithm_group_box.setSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        algorithm_selection_layout = QHBoxLayout(algorithm_group_box)
        self.dijkstra_radio_btn = QRadioButton(self)
        self.dijkstra_radio_btn.setText('Dijkstra')
        self.dijkstra_radio_btn.setChecked(True)
        self.bellman_radio_btn = QRadioButton(self)
        self.bellman_radio_btn.setText('Bellman-Ford')
        self.floyd_radio_btn = QRadioButton(self)
        self.floyd_radio_btn.setText('Floyd-Warshall')
        algorithm_selection_layout.addWidget(self.dijkstra_radio_btn)
        algorithm_selection_layout.addWidget(self.bellman_radio_btn)
        algorithm_selection_layout.addWidget(self.floyd_radio_btn)
        # chart and web view
        chart_and_web_widget = QWidget()
        self.chart_view = ChartView(title='Graph', parent=self)
        self.chart_view.nodeClicked.connect(self.render_web_ui)
        self.web_view = WebEngineView(self)
        chart_web_ui_layout = QHBoxLayout(chart_and_web_widget)
        chart_web_ui_layout.setContentsMargins(0, 0, 0, 0)
        chart_web_ui_layout.setSpacing(0)
        chart_web_ui_layout.addWidget(self.chart_view, 1)
        chart_web_ui_layout.addWidget(self.web_view, 1)
        # execute buttons
        open_osm_btn = QPushButton('Open OSM File', self)
        open_osm_btn.clicked.connect(self.load_osm_file)
        find_routes_btn = QPushButton('Find Routes', self)
        find_routes_btn.clicked.connect(self.run_shortest_path_algorithm)
        verify_result_btn = QPushButton('Find Routes with Online Map', self)
        verify_result_btn.clicked.connect(self.open_online_map_dialog)
        # add widgets
        layout.addWidget(chart_and_web_widget)
        layout.addWidget(algorithm_group_box)
        layout.addWidget(open_osm_btn)
        layout.addWidget(find_routes_btn)
        layout.addWidget(verify_result_btn)
        self.setCentralWidget(widget)
        self.showMaximized()

    def run_shortest_path_algorithm(self):
        if self.reader is None or len(self.index_to_marker_positions) != 2:
            return
        if self.dijkstra_radio_btn.isChecked():
            shortest_paths, distances = self.run_dijkstra_algorithm()
        elif self.bellman_radio_btn.isChecked():
            shortest_paths, distances = self.run_bellman_ford_algorithm()
        elif self.floyd_radio_btn.isChecked():
            shortest_paths = self.run_floyd_warshall_algorithm()
        else:
            assert False

        bounds = self.reader.get_array_bounds()
        view = [(bounds[0][0] + bounds[1][0]) / 2,
                (bounds[0][1] + bounds[1][1]) / 2]
        output_html = TEMPLATE.render(
            view=view, bounds=bounds,
            mark_positions=list(self.index_to_marker_positions.values()),
            paths=shortest_paths, distances=distances)
        self.web_view.set_html_content(output_html)

    def load_osm_file(self):
        if self.reader is not None:
            self.chart_view.reset()
        filepath = QFileDialog.getOpenFileName(
            self, "Open File", CURRENT_DIR, "OSM file (*.osm)")
        if os.path.isfile(filepath[0]):
            self.reader = pmd.OSMReader.parse(filepath[0])
            line_coordinates = self.reader.get_line_coordinates()
            node_coordinates = self.reader.get_node_coordinates()
            self.chart_view.plot(line_coordinates)
            self.chart_view.scatter(
                node_coordinates,
                node_infos=[(node.raw_lat, node.raw_lon)
                            for node in self.reader.index_to_node])
            #
            bounds = self.reader.get_array_bounds()
            view = [(bounds[0][0] + bounds[1][0]) / 2,
                    (bounds[0][1] + bounds[1][1]) / 2]
            output_html = TEMPLATE.render(view=view, bounds=bounds)
            self.web_view.set_html_content(output_html)

    def render_web_ui(self, node_index):
        if self.reader is not None:
            node = self.reader.index_to_node[node_index]
            if len(self.index_to_marker_positions) == 2:
                self.index_to_marker_positions.clear()
            self.index_to_marker_positions[node_index] = [
                node.raw_lat, node.raw_lon]
            #
            bounds = self.reader.get_array_bounds()
            view = [(bounds[0][0] + bounds[1][0]) / 2,
                    (bounds[0][1] + bounds[1][1]) / 2]
            output_html = TEMPLATE.render(
                view=view, bounds=bounds,
                mark_positions=list(self.index_to_marker_positions.values()))
            self.web_view.set_html_content(output_html)

    def open_online_map_dialog(self):
        dialog = OnlineMapDialog(self)
        marker_locations = list(self.index_to_marker_positions.values())
        dialog.find_best_way(
            start_loc=marker_locations[0], end_loc=marker_locations[1])
        dialog.show()

    def run_dijkstra_algorithm(self) -> tp.Tuple[list, list]:
        assert self.reader is not None
        graph = self.reader.convert_adjacency_matrix_to_dict()
        start_index, end_index = list(self.index_to_marker_positions.keys())
        path, distance = dijkstra.dijkstra(
            graph=graph, start=start_index, end=end_index)
        return [self.reader.get_coordinates_from_node_indices(path)], [distance]

    def run_bellman_ford_algorithm(self) -> tp.Tuple[list, list]:
        assert self.reader is not None
        graph = self.reader.convert_adjacency_matrix_to_dict()
        start_index, end_index = list(self.index_to_marker_positions.keys())
        path, distance = bellman_ford.bellman_ford(
            graph=graph, start=start_index, end=end_index)
        print(path)
        return [self.reader.get_coordinates_from_node_indices(path)], [distance]

    def run_floyd_warshall_algorithm(self) -> tp.Union[np.ndarray, list]:
        return []


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Application()
    sys.exit(app.exec())
