import sys
import typing as tp
import scipy.spatial as sp
import os
import numpy as np
import process_map_data as pmd
import dijkstra

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QWidget, QGroupBox,
    QRadioButton, QVBoxLayout, QHBoxLayout, QFileDialog, QSizePolicy
)
from PySide6.QtCore import QPointF, QObject, Signal
from PySide6.QtGui import QPainter
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCharts import QChartView, QChart, QLineSeries, QScatterSeries
from jinja2 import Environment, FileSystemLoader

# variables
current_dir = os.path.dirname(os.path.abspath(__file__))
file_loader = FileSystemLoader(current_dir)
env = Environment(loader=file_loader)


class WebEngineView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        self._browser = QWebEngineView(self)
        layout.addWidget(self._browser)
        self.setLayout(layout)

    def set_html_content(self, html: str):
        self._browser.setHtml(html)


class ScatterCommunicator(QObject):
    node_clicked_signal = Signal(int)


class ChartView(QWidget):
    def __init__(self, title=None, parent=None):
        super().__init__(parent)
        self._title = title
        self._scatter_series = QScatterSeries()
        self._scatter_series.setMarkerSize(10.0)
        self._scatter_series.doubleClicked.connect(self.on_double_clicked)
        self._chart_view = QChartView()
        self._chart_view.setRubberBand(QChartView.RubberBand.RectangleRubberBand)
        self._chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        #
        layout = QHBoxLayout()
        layout.addWidget(self._chart_view)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        # signals
        self.communicator = ScatterCommunicator()
        self.nodeDoubleClicked = self.communicator.node_clicked_signal
        #
        self._chart = None
        self.points = None
        self.kdtree = None

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

    def scatter(self, points: np.ndarray):
        assert points.shape[1] == 2
        if self.points is None:
            self.points = points
        self.kdtree = sp.KDTree(points)
        for point in points:
            self._scatter_series.append(*point)
        self._chart.addSeries(self._scatter_series)

    def on_double_clicked(self, point: QPointF):
        if self.kdtree is None:
            return
        x = point.x()
        y = point.y()
        node_index = self.kdtree.query([x, y], k=1)[1]
        self.nodeDoubleClicked.emit(node_index)


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
        algorithm_group_box.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
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
        self.chart_view.nodeDoubleClicked.connect(self.render_web_ui)
        self.web_view = WebEngineView(self)
        chart_web_ui_layout = QHBoxLayout(chart_and_web_widget)
        chart_web_ui_layout.setContentsMargins(0, 0, 0, 0)
        chart_web_ui_layout.setSpacing(0)
        chart_web_ui_layout.addWidget(self.chart_view, 1)
        chart_web_ui_layout.addWidget(self.web_view, 1)
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
        if self.reader is None or len(self.index_to_marker_positions) != 2:
            return
        if self.dijkstra_radio_btn.isChecked():
            shortest_paths, distances = self.run_dijkstra_algorithm()
        elif self.bellman_radio_btn.isChecked():
            shortest_paths = self.run_bellman_ford_algorithm()
        elif self.floyd_radio_btn.isChecked():
            shortest_paths = self.run_floyd_warshall_algorithm()
        else:
            assert False
        template = env.get_template('map_template.html')
        bounds = self.reader.get_array_bounds()
        view = [(bounds[0][0] + bounds[1][0]) / 2, (bounds[0][1] + bounds[1][1]) / 2]
        output_html = template.render(
            view=view, bounds=bounds,
            mark_positions=list(self.index_to_marker_positions.values()),
            paths=shortest_paths)
        self.web_view.set_html_content(output_html)

    def load_osm_file(self):
        filepath = QFileDialog.getOpenFileName(self, "Open File", "/home", "OSM file (*.osm)")
        if os.path.isfile(filepath[0]):
            self.reader = pmd.OSMReader.parse(filepath[0])
            line_coordinates = self.reader.get_line_coordinates()
            node_coordinates = self.reader.get_node_coordinates()
            self.chart_view.plot(line_coordinates)
            self.chart_view.scatter(node_coordinates)
            #
            template = env.get_template('map_template.html')
            bounds = self.reader.get_array_bounds()
            view = [(bounds[0][0] + bounds[1][0]) / 2, (bounds[0][1] + bounds[1][1]) / 2]
            output_html = template.render(view=view, bounds=bounds)
            self.web_view.set_html_content(output_html)

    def render_web_ui(self, node_index):
        if self.reader is not None:
            node = self.reader.index_to_node[node_index]
            lon = np.degrees(node.lon)
            lat = np.degrees(node.lat)
            if len(self.index_to_marker_positions) == 2:
                self.index_to_marker_positions.clear()
            self.index_to_marker_positions[node_index] = [lat, lon]
            #
            template = env.get_template('map_template.html')
            bounds = self.reader.get_array_bounds()
            view = [(bounds[0][0] + bounds[1][0]) / 2, (bounds[0][1] + bounds[1][1]) / 2]
            output_html = template.render(
                view=view, bounds=bounds,
                mark_positions=list(self.index_to_marker_positions.values()))
            self.web_view.set_html_content(output_html)

    def run_dijkstra_algorithm(self) -> tp.Tuple[list, list]:
        assert self.reader is not None
        graph = self.reader.convert_adjacency_matrix_to_dict()
        start_index, end_index = list(self.index_to_marker_positions.keys())
        path, distance = dijkstra.dijkstra(graph=graph, start=start_index, end=end_index)
        return [self.reader.get_coordinates_from_node_indices(path)], [distance]

    def run_bellman_ford_algorithm(self) -> tp.Union[np.ndarray, list]:
        return []

    def run_floyd_warshall_algorithm(self) -> tp.Union[np.ndarray, list]:
        return []


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Application()
    sys.exit(app.exec())
