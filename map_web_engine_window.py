import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl


class MapWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Route Mapper")
        self.setGeometry(100, 100, 800, 600)

        # Create a central widget and layout
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        # Create a web engine view to display the map
        self.map_view = QWebEngineView()
        self.map_view.loadFinished.connect(self.printf)
        layout.addWidget(self.map_view)

        # Add a button to draw the route
        self.route_button = QPushButton("Draw Route")
        self.route_button.clicked.connect(self.draw_route)
        layout.addWidget(self.route_button)

        self.setCentralWidget(central_widget)

    def draw_route(self):
        # Replace latitudes and longitudes with your desired points
        start_lat, start_lon = 10.7857536, 106.6669098  # Le Thi Rieng park
        end_lat, end_lon = 10.7713016, 106.6578284  # Bach Khoa

        # Generate a URL to display the route using OpenStreetMap
        route_url = f"https://www.openstreetmap.org/directions?engine=fossgis_osrm_car&route={start_lat}%2C{start_lon}%3B{end_lat}%2C{end_lon}"

        # Load the URL in the web engine view
        self.map_view.load(QUrl(route_url))

    def printf(self, *args):
        print(args)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MapWindow()
    window.show()
    sys.exit(app.exec_())
