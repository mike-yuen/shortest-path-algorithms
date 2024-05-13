import typing as tp
import osmium
import math
import numpy as np
import matplotlib.pyplot as plt


__all__ = ['get_adjacency_matrix_from_osm_file']

R = 6371  # Earth's radius in kilometers


class Node(tp.NamedTuple):
    id: int
    lon: float
    lat: float
    name: tp.Union[str, None]

    # Function to convert latitude and longitude to Cartesian coordinates
    def to_cartesian(self):
        x = R * math.cos(self.lat) * math.cos(self.lon)
        y = R * math.cos(self.lat) * math.sin(self.lon)
        z = R * math.sin(self.lat)
        return x, y, z


class Edge(tp.NamedTuple):
    id: str
    nodes: tp.Tuple[Node, Node]
    name: str

    def distance(self) -> float:
        node1, node2 = self.nodes
        lat1 = node1.lat
        lat2 = node2.lat
        lon1 = node1.lon
        lon2 = node2.lon
        delta_lat = abs(lat2 - lat1)
        delta_lon = abs(lon2 - lon1)
        a = np.sin(delta_lat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(delta_lon / 2) ** 2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        d = R * c
        return d


class OSMProcessHandler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.streets = []
        self.id_to_node = {}
        self.id_to_node_index = {}
        self.node_coordinates = []
        self.pair_coordinates = []

    def node(self, n):
        # Define your filtering criteria here
        self.id_to_node[n.id] = Node(
            id=n.id, lon=np.radians(n.location.lon),
            lat=np.radians(n.location.lat), name=n.tags.get('name', ''))

    def way(self, way):
        node_refs = way.nodes
        node_ref0 = node_refs[0]
        node_ref1 = node_refs[-1]
        if node_ref0.ref == node_ref1.ref:
            # self-loop node
            return None
        street_name = way.tags.get('addr:street', None)
        if street_name is None:
            street_name = way.tags.get('name', '')
        node0 = Node(
            id=node_ref0.ref, lon=self.id_to_node[node_ref0.ref].lon,
            lat=self.id_to_node[node_ref0.ref].lat, name=way.tags.get('name', ''))
        node1 = Node(
            id=node_ref1.ref, lon=self.id_to_node[node_ref1.ref].lon,
            lat=self.id_to_node[node_ref1.ref].lat, name=way.tags.get('name', ''))
        temp = []
        for node in [node0, node1]:
            if node.id not in self.id_to_node_index:
                self.id_to_node_index[node.id] = len(self.id_to_node_index)
                self.node_coordinates.append(list(node.to_cartesian()[:-1]))
            temp.append(list(node.to_cartesian()[:-1]))
        self.pair_coordinates.append(temp)
        street = Edge(
            id=way.id, name=street_name, nodes=(node0, node1))
        self.streets.append(street)


def get_adjacency_matrix_from_osm_file(filename: str) -> np.ndarray:
    # Parse .osm file and apply filters
    osm_handler = OSMProcessHandler()
    osm_handler.apply_file(filename)
    node_coordinates = np.array(osm_handler.node_coordinates)
    plt.figure(figsize=(8, 6))
    plt.scatter(node_coordinates[:, 0], node_coordinates[:, 1], color='blue', label='Random Data')
    # Show plot
    pair_coordinates = np.array(osm_handler.pair_coordinates)
    for pair in pair_coordinates:
        plt.plot(
            pair[:, 0], pair[:, 1],
            color='red', label='Sine Curve', linestyle='-')
    plt.grid(True)
    plt.show()
    edges = osm_handler.streets
    print('>>', len(edges))
    id_to_node_index = osm_handler.id_to_node_index
    num_node = len(id_to_node_index)
    adjacency_matrix = np.zeros((num_node, num_node))
    for edge in edges:
        nodes = edge.nodes
        node0_id = nodes[0].id
        node1_id = nodes[1].id
        node0_idx = id_to_node_index[node0_id]
        node1_idx = id_to_node_index[node1_id]
        adjacency_matrix[node0_idx, node1_idx] = edge.distance()
    return adjacency_matrix

print(get_adjacency_matrix_from_osm_file('data/exported_map.osm.osm').shape)