import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView


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


class MapWindow(QMainWindow):
    def __init__(self, path):
        super().__init__()
        self.setWindowTitle("OpenStreetMap with Path")
        self.setGeometry(100, 100, 800, 600)

        html_content = generate_map_html(path)

        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)
        self.browser.setHtml(html_content)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    path = [(10.7622564, 106.6569704),
            (10.7621586, 106.6570011),
            (10.7689823, 106.6525092),
            (10.7694154, 106.6525035),
            (10.7711526, 106.6529604),
            (10.7704293, 106.6577405),
            ]
    window = MapWindow(path)
    window.show()
    sys.exit(app.exec_())
